# Copyright (c) 2026, PT Palma Progress Shipyard and contributors
# For license information, please see license.txt


import copy
from collections import defaultdict

import frappe
from frappe import _
from frappe.query_builder.functions import CombineDatetime, Sum
from frappe.utils import cint, flt, get_datetime

from erpnext.stock.doctype.inventory_dimension.inventory_dimension import get_inventory_dimensions
from erpnext.stock.doctype.serial_no.serial_no import get_serial_nos
from erpnext.stock.doctype.stock_reconciliation.stock_reconciliation import get_stock_balance_for
from erpnext.stock.doctype.warehouse.warehouse import apply_warehouse_filter
from erpnext.stock.utils import (
	is_reposting_item_valuation_in_progress,
	update_included_uom_in_report,
)


def execute(filters=None):
	is_reposting_item_valuation_in_progress()
	include_uom = filters.get("include_uom")
	columns = get_columns(filters)
	items = get_items(filters)
	sl_entries = get_stock_ledger_entries(filters, items)
	sl_entries, opening_fifo_queues = enrich_sl_entries_with_procurement_details(sl_entries, filters, items)
	item_details = get_item_details(items, sl_entries, include_uom)
	if filters.get("batch_no"):
		opening_row = get_opening_balance_from_batch(filters, columns, sl_entries)
	else:
		opening_row = get_opening_balance(filters, columns, sl_entries)

	precision = cint(frappe.db.get_single_value("System Settings", "float_precision"))
	bundle_details = {}

	if filters.get("segregate_serial_batch_bundle"):
		bundle_details = get_serial_batch_bundle_details(sl_entries, filters)

	data = []
	conversion_factors = []
	if opening_row:
		data.append(opening_row)
		conversion_factors.append(0)

	actual_qty = stock_value = 0
	if opening_row:
		actual_qty = opening_row.get("qty_after_transaction")
		stock_value = opening_row.get("stock_value")

	available_serial_nos = {}
	inventory_dimension_filters_applied = check_inventory_dimension_filters_applied(filters)

	batch_balance_dict = frappe._dict({})
	if actual_qty and filters.get("batch_no"):
		batch_balance_dict[filters.batch_no] = [actual_qty, stock_value]

	for sle in sl_entries:
		item_detail = item_details[sle.item_code]

		sle.update(item_detail)
		if bundle_info := bundle_details.get(sle.serial_and_batch_bundle):
			data.extend(get_segregated_bundle_entries(sle, bundle_info, batch_balance_dict, filters))
			continue

		if filters.get("batch_no") or inventory_dimension_filters_applied:
			actual_qty += flt(sle.actual_qty, precision)
			stock_value += sle.stock_value_difference
			if sle.batch_no:
				if not batch_balance_dict.get(sle.batch_no):
					batch_balance_dict[sle.batch_no] = [0, 0]

				batch_balance_dict[sle.batch_no][0] += sle.actual_qty

			if filters.get("segregate_serial_batch_bundle"):
				actual_qty = batch_balance_dict[sle.batch_no][0]

			if sle.voucher_type == "Stock Reconciliation" and not sle.actual_qty:
				actual_qty = sle.qty_after_transaction
				stock_value = sle.stock_value

			sle.update({"qty_after_transaction": actual_qty, "stock_value": stock_value})

		sle.update({"in_qty": max(sle.actual_qty, 0), "out_qty": min(sle.actual_qty, 0)})

		if sle.serial_no:
			update_available_serial_nos(available_serial_nos, sle)

		if sle.actual_qty:
			sle["in_out_rate"] = flt(sle.stock_value_difference / sle.actual_qty, precision)

		elif sle.voucher_type == "Stock Reconciliation":
			sle["in_out_rate"] = sle.valuation_rate

		data.append(sle)

		if include_uom:
			conversion_factors.append(item_detail.conversion_factor)

	for row in data:
		row["usd_currency"] = "USD"

	update_included_uom_in_report(columns, data, include_uom, conversion_factors)

	if filters.get("show_tree_view"):
		data = convert_to_tree_view(data, item_details, filters, opening_fifo_queues)
		for col in columns:
			if col.get("fieldname") == "date":
				col["fieldtype"] = "Data"

	return columns, data


def get_segregated_bundle_entries(sle, bundle_details, batch_balance_dict, filters):
	segregated_entries = []
	qty_before_transaction = sle.qty_after_transaction - sle.actual_qty
	stock_value_before_transaction = sle.stock_value - sle.stock_value_difference

	for row in bundle_details:
		new_sle = copy.deepcopy(sle)
		new_sle.update(row)
		new_sle.update(
			{
				"in_out_rate": flt(new_sle.stock_value_difference / row.qty) if row.qty else 0,
				"in_qty": row.qty if row.qty > 0 else 0,
				"out_qty": row.qty if row.qty < 0 else 0,
				"qty_after_transaction": qty_before_transaction + row.qty,
				"stock_value": stock_value_before_transaction + new_sle.stock_value_difference,
				"incoming_rate": row.incoming_rate if row.qty > 0 else 0,
			}
		)

		if filters.get("batch_no") and row.batch_no:
			if not batch_balance_dict.get(row.batch_no):
				batch_balance_dict[row.batch_no] = [0, 0]

			batch_balance_dict[row.batch_no][0] += row.qty
			batch_balance_dict[row.batch_no][1] += row.stock_value_difference

			new_sle.update(
				{
					"qty_after_transaction": batch_balance_dict[row.batch_no][0],
					"stock_value": batch_balance_dict[row.batch_no][1],
				}
			)

		qty_before_transaction += row.qty
		stock_value_before_transaction += new_sle.stock_value_difference

		new_sle.valuation_rate = (
			stock_value_before_transaction / qty_before_transaction if qty_before_transaction else 0
		)

		segregated_entries.append(new_sle)

	return segregated_entries


def get_serial_batch_bundle_details(sl_entries, filters=None):
	bundle_details = []
	for sle in sl_entries:
		if sle.serial_and_batch_bundle:
			bundle_details.append(sle.serial_and_batch_bundle)

	if not bundle_details:
		return frappe._dict({})

	query_filers = {"parent": ("in", bundle_details)}
	if filters.get("batch_no"):
		query_filers["batch_no"] = filters.batch_no

	_bundle_details = frappe._dict({})
	batch_entries = frappe.get_all(
		"Serial and Batch Entry",
		filters=query_filers,
		fields=["parent", "qty", "incoming_rate", "stock_value_difference", "batch_no", "serial_no"],
		order_by="parent, idx",
	)
	for entry in batch_entries:
		_bundle_details.setdefault(entry.parent, []).append(entry)

	return _bundle_details


def update_available_serial_nos(available_serial_nos, sle):
	serial_nos = get_serial_nos(sle.serial_no)
	key = (sle.item_code, sle.warehouse)
	if key not in available_serial_nos:
		stock_balance = get_stock_balance_for(
			sle.item_code, sle.warehouse, sle.posting_date, sle.posting_time
		)
		serials = get_serial_nos(stock_balance["serial_nos"]) if stock_balance["serial_nos"] else []
		available_serial_nos.setdefault(key, serials)

	existing_serial_no = available_serial_nos[key]
	for sn in serial_nos:
		if sle.actual_qty > 0:
			if sn in existing_serial_no:
				existing_serial_no.remove(sn)
			else:
				existing_serial_no.append(sn)
		else:
			if sn in existing_serial_no:
				existing_serial_no.remove(sn)
			else:
				existing_serial_no.append(sn)

	sle.balance_serial_no = "\n".join(existing_serial_no)


def get_columns(filters):
	columns = [
		{"label": _("Date"), "fieldname": "date", "fieldtype": "Datetime", "width": 150},
		{"label": _("Posting Date"), "fieldname": "posting_date", "fieldtype": "Date", "width": 100},
		{"label": _("Posting Time"), "fieldname": "posting_time", "fieldtype": "Time", "width": 100},
		{
			"label": _("Item"),
			"fieldname": "item_code",
			"fieldtype": "Link",
			"options": "Item",
			"width": 100,
		},
		{"label": _("Item Name"), "fieldname": "item_name", "width": 100},
		{
			"label": _("Stock UOM"),
			"fieldname": "stock_uom",
			"fieldtype": "Link",
			"options": "UOM",
			"width": 90,
		},
	]

	for dimension in get_inventory_dimensions():
		columns.append(
			{
				"label": _(dimension.doctype),
				"fieldname": dimension.fieldname,
				"fieldtype": "Link",
				"options": dimension.doctype,
				"width": 110,
			}
		)

	columns.extend(
		[
			{
				"label": _("In Qty"),
				"fieldname": "in_qty",
				"fieldtype": "Float",
				"width": 80,
				"convertible": "qty",
			},
			{
				"label": _("Out Qty"),
				"fieldname": "out_qty",
				"fieldtype": "Float",
				"width": 80,
				"convertible": "qty",
			},
			{
				"label": _("Balance Qty"),
				"fieldname": "qty_after_transaction",
				"fieldtype": "Float",
				"width": 100,
				"convertible": "qty",
			},
			{
				"label": _("Warehouse"),
				"fieldname": "warehouse",
				"fieldtype": "Link",
				"options": "Warehouse",
				"width": 150,
			},
			{
				"label": _("Item Group"),
				"fieldname": "item_group",
				"fieldtype": "Link",
				"options": "Item Group",
				"width": 100,
			},
			{
				"label": _("Brand"),
				"fieldname": "brand",
				"fieldtype": "Link",
				"options": "Brand",
				"width": 100,
			},
			{"label": _("Description"), "fieldname": "description", "width": 200},
			{
				"label": _("Incoming Rate"),
				"fieldname": "incoming_rate",
				"fieldtype": "Currency",
				"width": 110,
				"options": "Company:company:default_currency",
				"convertible": "rate",
			},
			{
				"label": _("Avg Rate (Balance Stock)"),
				"fieldname": "valuation_rate",
				"fieldtype": filters.valuation_field_type,
				"width": 180,
				"options": "Company:company:default_currency"
				if filters.valuation_field_type == "Currency"
				else None,
				"convertible": "rate",
			},
			{
				"label": _("Valuation Rate"),
				"fieldname": "in_out_rate",
				"fieldtype": filters.valuation_field_type,
				"width": 140,
				"options": "Company:company:default_currency"
				if filters.valuation_field_type == "Currency"
				else None,
				"convertible": "rate",
			},
			{
				"label": _("Balance Value"),
				"fieldname": "stock_value",
				"fieldtype": "Currency",
				"width": 110,
				"options": "Company:company:default_currency",
			},
			{
				"label": _("Value Change"),
				"fieldname": "stock_value_difference",
				"fieldtype": "Currency",
				"width": 110,
				"options": "Company:company:default_currency",
			},
			{"label": _("Voucher Type"), "fieldname": "voucher_type", "width": 110},
			{
				"label": _("Voucher #"),
				"fieldname": "voucher_no",
				"fieldtype": "Dynamic Link",
				"options": "voucher_type",
				"width": 100,
			},
			{
				"label": _("Batch"),
				"fieldname": "batch_no",
				"fieldtype": "Link",
				"options": "Batch",
				"width": 100,
			},
			{
				"label": _("Serial No"),
				"fieldname": "serial_no",
				"fieldtype": "Link",
				"options": "Serial No",
				"width": 100,
			},
			{
				"label": _("Serial and Batch Bundle"),
				"fieldname": "serial_and_batch_bundle",
				"fieldtype": "Link",
				"options": "Serial and Batch Bundle",
				"width": 100,
			},
			{
				"label": _("Project"),
				"fieldname": "project",
				"fieldtype": "Link",
				"options": "Project",
				"width": 100,
			},
			{
				"label": _("Company"),
				"fieldname": "company",
				"fieldtype": "Link",
				"options": "Company",
				"width": 110,
			},
			{"label": _("PO No"), "fieldname": "purchase_order", "fieldtype": "Link", "options": "Purchase Order", "width": 120},
			{"label": _("PO Date"), "fieldname": "po_date", "fieldtype": "Date", "width": 100},
			{"label": _("PR No"), "fieldname": "purchase_receipt", "fieldtype": "Link", "options": "Purchase Receipt", "width": 120},
			{"label": _("PR Date"), "fieldname": "pr_date", "fieldtype": "Date", "width": 100},
			{"label": _("Vendor Currency"), "fieldname": "vendor_currency", "fieldtype": "Link", "options": "Currency", "width": 80},
			{"label": _("Vendor Rate"), "fieldname": "vendor_rate", "fieldtype": "Currency", "options": "vendor_currency", "width": 120},
			{"label": _("IDR Rate"), "fieldname": "idr_rate", "fieldtype": "Currency", "options": "Company:company:default_currency", "width": 120},
			{"label": _("IDR Amount"), "fieldname": "idr_amount", "fieldtype": "Currency", "options": "Company:company:default_currency", "width": 130},
			{"label": _("USD Rate"), "fieldname": "usd_rate", "fieldtype": "Data", "width": 120},
			{"label": _("USD Amount"), "fieldname": "usd_amount", "fieldtype": "Data", "width": 130},
			{"label": _("Currency Exchange Ref"), "fieldname": "currency_exchange_ref", "fieldtype": "Link", "options": "Currency Exchange", "width": 160},
			{"label": _("Exchange Rate (USD to IDR)"), "fieldname": "exchange_rate_value", "fieldtype": "Currency", "width": 150},
			{"label": _("PI No"), "fieldname": "purchase_invoice", "fieldtype": "Link", "options": "Purchase Invoice", "width": 120},
			{"label": _("PI Date"), "fieldname": "pi_date", "fieldtype": "Date", "width": 100},
		]
	)

	# Append custom Stock Reconciliation Item columns at the end
	columns.extend(
		[
			{"label": _("SR Kode Lama"), "fieldname": "custom_sr_kode_lama", "fieldtype": "Data", "width": 120},
			{"label": _("SR No RDO"), "fieldname": "custom_sr_no_rdo", "fieldtype": "Data", "width": 120},
			{"label": _("SR Tanggal RDO"), "fieldname": "custom_sr_tanggal_rdo", "fieldtype": "Date", "width": 100},
			{"label": _("SR No RIO"), "fieldname": "custom_sr_no_rio", "fieldtype": "Data", "width": 120},
			{"label": _("SR Tanggal RIO"), "fieldname": "custom_sr_tanggal_rio", "fieldtype": "Date", "width": 100},
			{"label": _("SR Transaction Type"), "fieldname": "custom_sr_transaction_type", "fieldtype": "Select", "width": 120},
			{"label": _("SR Supplier Historis"), "fieldname": "custom_sr_supplier_historis", "fieldtype": "Data", "width": 150},
			{"label": _("SR No PIB"), "fieldname": "custom_sr_no_pib", "fieldtype": "Data", "width": 120},
			{"label": _("SR Tahun PIB"), "fieldname": "custom_sr_tahun_pib", "fieldtype": "Data", "width": 100},
			{"label": _("SR Bulan PIB"), "fieldname": "custom_sr_bulan_pib", "fieldtype": "Select", "width": 100},
			{"label": _("SR Tanggal PIB"), "fieldname": "custom_sr_tanggal_pib", "fieldtype": "Date", "width": 100},
			{"label": _("SR Kurs pada PIB"), "fieldname": "custom_sr_kurs_pada_pib", "fieldtype": "Currency", "width": 120},
			{"label": _("SR No Invoice Vendor"), "fieldname": "custom_sr_no_invoice_vendor", "fieldtype": "Data", "width": 130},
			{"label": _("SR Tahun doc RDO"), "fieldname": "custom_sr_tahun_doc_rdo", "fieldtype": "Int", "width": 100},
			{"label": _("SR Qty Invoice"), "fieldname": "custom_sr_qty_invoice", "fieldtype": "Data", "width": 110},
			{"label": _("SR Supplier Currency"), "fieldname": "custom_sr_supplier_currency", "fieldtype": "Link", "options": "Currency", "width": 100},
			{"label": _("SR Harga Supplier"), "fieldname": "custom_sr_harga_supplier", "fieldtype": "Currency", "options": "custom_sr_supplier_currency", "width": 120},
			{"label": _("SR Total dari Supplier"), "fieldname": "custom_sr_total_dari_supplier", "fieldtype": "Currency", "options": "custom_sr_supplier_currency", "width": 130},
			{"label": _("SR Kurs ke IDR"), "fieldname": "custom_sr_kurs_ke_idr", "fieldtype": "Currency", "width": 120},
			{"label": _("SR Kurs ke USD"), "fieldname": "custom_sr_kurs_ke_usd", "fieldtype": "Float", "width": 100},
			{"label": _("SR Total in USD"), "fieldname": "custom_sr_total_in_usd", "fieldtype": "Currency", "options": "usd_currency", "width": 120},
		]
	)

	return columns


def get_stock_ledger_entries(filters, items):
	from_date = get_datetime(filters.from_date + " 00:00:00")
	to_date = get_datetime(filters.to_date + " 23:59:59")

	sle = frappe.qb.DocType("Stock Ledger Entry")
	sri = frappe.qb.DocType("Stock Reconciliation Item")
	
	query = (
		frappe.qb.from_(sle)
		.left_join(sri)
		.on((sle.voucher_detail_no == sri.name) & (sle.voucher_type == "Stock Reconciliation"))
		.select(
			sle.name,
			sle.item_code,
			sle.posting_datetime.as_("date"),
			sle.warehouse,
			sle.posting_date,
			sle.posting_time,
			sle.actual_qty,
			sle.incoming_rate,
			sle.valuation_rate,
			sle.company,
			sle.voucher_type,
			sle.qty_after_transaction,
			sle.stock_value_difference,
			sle.serial_and_batch_bundle,
			sle.voucher_no,
			sle.stock_value,
			sle.batch_no,
			sle.serial_no,
			sle.project,
			sle.voucher_detail_no,
			sri.custom_sr_kode_lama,
			sri.custom_sr_no_rdo,
			sri.custom_sr_tanggal_rdo,
			sri.custom_sr_no_rio,
			sri.custom_sr_tanggal_rio,
			sri.custom_sr_transaction_type,
			sri.custom_sr_supplier_historis,
			sri.custom_sr_no_pib,
			sri.custom_sr_tahun_pib,
			sri.custom_sr_bulan_pib,
			sri.custom_sr_tanggal_pib,
			sri.custom_sr_kurs_pada_pib,
			sri.custom_sr_no_invoice_vendor,
			sri.custom_sr_tahun_doc_rdo,
			sri.custom_sr_qty_invoice,
			sri.custom_sr_supplier_currency,
			sri.custom_sr_harga_supplier,
			sri.custom_sr_total_dari_supplier,
			sri.custom_sr_kurs_ke_idr,
			sri.custom_sr_kurs_ke_usd,
			sri.custom_sr_total_in_usd,
		)
		.where((sle.docstatus < 2) & (sle.is_cancelled == 0) & (sle.posting_datetime[from_date:to_date]))
		.orderby(sle.posting_date)
		.orderby(sle.posting_time)
		.orderby(sle.creation)
	)

	inventory_dimension_fields = get_inventory_dimension_fields()
	if inventory_dimension_fields:
		for fieldname in inventory_dimension_fields:
			query = query.select(getattr(sle, fieldname))
			if fieldname in filters and filters.get(fieldname):
				query = query.where(getattr(sle, fieldname).isin(filters.get(fieldname)))

	if items:
		query = query.where(sle.item_code.isin(items))

	for field in ["voucher_no", "project", "company"]:
		if filters.get(field) and field not in inventory_dimension_fields:
			query = query.where(getattr(sle, field) == filters.get(field))

	if filters.get("batch_no"):
		bundles = get_serial_and_batch_bundles(filters)

		if bundles:
			query = query.where(
				(sle.serial_and_batch_bundle.isin(bundles)) | (sle.batch_no == filters.batch_no)
			)
		else:
			query = query.where(sle.batch_no == filters.batch_no)

	query = apply_warehouse_filter(query, sle, filters)

	return query.run(as_dict=True)


def get_serial_and_batch_bundles(filters):
	SBB = frappe.qb.DocType("Serial and Batch Bundle")
	SBE = frappe.qb.DocType("Serial and Batch Entry")

	query = (
		frappe.qb.from_(SBE)
		.inner_join(SBB)
		.on(SBE.parent == SBB.name)
		.select(SBE.parent)
		.where(
			(SBB.docstatus == 1)
			& (SBB.has_batch_no == 1)
			& (SBB.voucher_no.notnull())
			& (SBE.batch_no == filters.batch_no)
		)
	)

	return query.run(pluck=SBE.parent)


def get_inventory_dimension_fields():
	return [dimension.fieldname for dimension in get_inventory_dimensions()]


def get_items(filters):
	item = frappe.qb.DocType("Item")
	query = frappe.qb.from_(item).select(item.name)
	conditions = []

	if item_code := filters.get("item_code"):
		conditions.append(item.name == item_code)
	else:
		if brand := filters.get("brand"):
			conditions.append(item.brand == brand)
		if item_group := filters.get("item_group"):
			if condition := get_item_group_condition(item_group, item):
				conditions.append(condition)

	items = []
	if conditions:
		for condition in conditions:
			query = query.where(condition)
		items = [r[0] for r in query.run()]

	return items


def get_item_details(items, sl_entries, include_uom):
	item_details = {}
	if not items:
		items = list(set(d.item_code for d in sl_entries))

	if not items:
		return item_details

	item = frappe.qb.DocType("Item")
	query = (
		frappe.qb.from_(item)
		.select(item.name, item.item_name, item.description, item.item_group, item.brand, item.stock_uom)
		.where(item.name.isin(items))
	)

	if include_uom:
		ucd = frappe.qb.DocType("UOM Conversion Detail")
		query = (
			query.left_join(ucd)
			.on((ucd.parent == item.name) & (ucd.uom == include_uom))
			.select(ucd.conversion_factor)
		)

	res = query.run(as_dict=True)

	for item in res:
		item_details.setdefault(item.name, item)

	return item_details


def get_sle_conditions(filters):
	conditions = []
	if filters.get("warehouse"):
		warehouse_condition = get_warehouse_condition(filters.get("warehouse"))
		if warehouse_condition:
			conditions.append(warehouse_condition)
	if filters.get("voucher_no"):
		conditions.append("voucher_no=%(voucher_no)s")
	if filters.get("batch_no"):
		conditions.append("batch_no=%(batch_no)s")
	if filters.get("project"):
		conditions.append("project=%(project)s")

	for dimension in get_inventory_dimensions():
		if filters.get(dimension.fieldname):
			conditions.append(f"{dimension.fieldname} in %({dimension.fieldname})s")

	return "and {}".format(" and ".join(conditions)) if conditions else ""


def get_opening_balance_from_batch(filters, columns, sl_entries):
	query_filters = {
		"batch_no": filters.batch_no,
		"docstatus": 1,
		"is_cancelled": 0,
		"posting_date": ("<", filters.from_date),
		"company": filters.company,
	}

	for fields in ["item_code", "warehouse"]:
		if filters.get(fields):
			query_filters[fields] = filters.get(fields)

	opening_data = frappe.get_all(
		"Stock Ledger Entry",
		fields=["sum(actual_qty) as qty_after_transaction", "sum(stock_value_difference) as stock_value"],
		filters=query_filters,
	)[0]

	for field in ["qty_after_transaction", "stock_value", "valuation_rate"]:
		if opening_data.get(field) is None:
			opening_data[field] = 0.0

	table = frappe.qb.DocType("Stock Ledger Entry")
	sabb_table = frappe.qb.DocType("Serial and Batch Entry")
	query = (
		frappe.qb.from_(table)
		.inner_join(sabb_table)
		.on(table.serial_and_batch_bundle == sabb_table.parent)
		.select(
			Sum(sabb_table.qty).as_("qty"),
			Sum(sabb_table.stock_value_difference).as_("stock_value"),
		)
		.where(
			(sabb_table.batch_no == filters.batch_no)
			& (sabb_table.docstatus == 1)
			& (table.posting_date < filters.from_date)
			& (table.is_cancelled == 0)
		)
	)

	for field in ["item_code", "warehouse", "company"]:
		if filters.get(field):
			query = query.where(table[field] == filters.get(field))

	bundle_data = query.run(as_dict=True)

	if bundle_data:
		opening_data.qty_after_transaction += flt(bundle_data[0].qty)
		opening_data.stock_value += flt(bundle_data[0].stock_value)
		if opening_data.qty_after_transaction:
			opening_data.valuation_rate = flt(opening_data.stock_value) / flt(
				opening_data.qty_after_transaction
			)

	return {
		"item_code": _("'Opening'"),
		"qty_after_transaction": opening_data.qty_after_transaction,
		"valuation_rate": opening_data.valuation_rate,
		"stock_value": opening_data.stock_value,
	}


def get_opening_balance(filters, columns, sl_entries):
	if not (filters.item_code and filters.warehouse and filters.from_date):
		return

	from erpnext.stock.stock_ledger import get_previous_sle

	last_entry = get_previous_sle(
		{
			"item_code": filters.item_code,
			"warehouse_condition": get_warehouse_condition(filters.warehouse),
			"posting_date": filters.from_date,
			"posting_time": "00:00:00",
		}
	)

	# check if any SLEs are actually Opening Stock Reconciliation
	for sle in list(sl_entries):
		if (
			sle.get("voucher_type") == "Stock Reconciliation"
			and sle.posting_date == filters.from_date
			and frappe.db.get_value("Stock Reconciliation", sle.voucher_no, "purpose") == "Opening Stock"
		):
			last_entry = sle
			sl_entries.remove(sle)

	row = {
		"item_code": _("'Opening'"),
		"qty_after_transaction": last_entry.get("qty_after_transaction", 0),
		"valuation_rate": last_entry.get("valuation_rate", 0),
		"stock_value": last_entry.get("stock_value", 0),
	}

	return row


def get_warehouse_condition(warehouse):
	warehouse_details = frappe.db.get_value("Warehouse", warehouse, ["lft", "rgt"], as_dict=1)
	if warehouse_details:
		return f" exists (select name from `tabWarehouse` wh \
			where wh.lft >= {warehouse_details.lft} and wh.rgt <= {warehouse_details.rgt} and warehouse = wh.name)"

	return ""


def get_item_group_condition(item_group, item_table=None):
	item_group_details = frappe.db.get_value("Item Group", item_group, ["lft", "rgt"], as_dict=1)
	if item_group_details:
		if item_table:
			ig = frappe.qb.DocType("Item Group")
			return item_table.item_group.isin(
				frappe.qb.from_(ig)
				.select(ig.name)
				.where(
					(ig.lft >= item_group_details.lft)
					& (ig.rgt <= item_group_details.rgt)
					& (item_table.item_group == ig.name)
				)
			)
		else:
			return f"item.item_group in (select ig.name from `tabItem Group` ig \
				where ig.lft >= {item_group_details.lft} and ig.rgt <= {item_group_details.rgt} and item.item_group = ig.name)"


def check_inventory_dimension_filters_applied(filters) -> bool:
	for dimension in get_inventory_dimensions():
		if dimension.fieldname in filters and filters.get(dimension.fieldname):
			return True

	return False


def get_all_sles_for_fifo(filters, items):
	to_date = get_datetime(filters.to_date + " 23:59:59")
	sle = frappe.qb.DocType("Stock Ledger Entry")
	sri = frappe.qb.DocType("Stock Reconciliation Item")
	
	query = (
		frappe.qb.from_(sle)
		.left_join(sri)
		.on((sle.voucher_detail_no == sri.name) & (sle.voucher_type == "Stock Reconciliation"))
		.select(
			sle.name, sle.item_code, sle.warehouse, sle.posting_datetime,
			sle.actual_qty, sle.valuation_rate, sle.incoming_rate,
			sle.voucher_type, sle.voucher_no, sle.voucher_detail_no,
			sle.posting_date, sle.posting_time, sle.creation,
			sri.custom_sr_kode_lama,
			sri.custom_sr_no_rdo,
			sri.custom_sr_tanggal_rdo,
			sri.custom_sr_no_rio,
			sri.custom_sr_tanggal_rio,
			sri.custom_sr_transaction_type,
			sri.custom_sr_supplier_historis,
			sri.custom_sr_no_pib,
			sri.custom_sr_tahun_pib,
			sri.custom_sr_bulan_pib,
			sri.custom_sr_tanggal_pib,
			sri.custom_sr_kurs_pada_pib,
			sri.custom_sr_no_invoice_vendor,
			sri.custom_sr_tahun_doc_rdo,
			sri.custom_sr_qty_invoice,
			sri.custom_sr_supplier_currency,
			sri.custom_sr_harga_supplier,
			sri.custom_sr_total_dari_supplier,
			sri.custom_sr_kurs_ke_idr,
			sri.custom_sr_kurs_ke_usd,
			sri.custom_sr_total_in_usd
		)
		.where((sle.docstatus < 2) & (sle.is_cancelled == 0) & (sle.posting_datetime <= to_date))
		.orderby(sle.posting_date)
		.orderby(sle.posting_time)
		.orderby(sle.creation)
	)
	if items:
		query = query.where(sle.item_code.isin(items))
	if filters.get("warehouse"):
		query = query.where(sle.warehouse == filters.warehouse)
	
	return query.run(as_dict=True)

def enrich_sl_entries_with_procurement_details(sl_entries, filters, items):
	all_sles = get_all_sles_for_fifo(filters, items)
	if not all_sles:
		return sl_entries, {}
	
	# Fetch all required procurement details
	pr_item_ids = [s.voucher_detail_no for s in all_sles if s.voucher_type == 'Purchase Receipt' and s.voucher_detail_no]
	pi_item_ids = [s.voucher_detail_no for s in all_sles if s.voucher_type == 'Purchase Invoice' and s.voucher_detail_no]

	pr_items = {}
	if pr_item_ids:
		res = frappe.get_all(
			"Purchase Receipt Item",
			filters={"name": ("in", pr_item_ids)},
			fields=["name", "purchase_order", "rate", "base_rate", "base_amount", "parent"]
		)
		pr_items = {d.name: d for d in res}

	pi_items = {}
	if pi_item_ids:
		res = frappe.get_all(
			"Purchase Invoice Item",
			filters={"name": ("in", pi_item_ids)},
			fields=["name", "purchase_order", "purchase_receipt", "rate", "base_rate", "base_amount", "parent"]
		)
		pi_items = {d.name: d for d in res}

	po_names = set()
	pr_names = set()
	pi_names = set()

	for item in pr_items.values():
		if item.purchase_order:
			po_names.add(item.purchase_order)
		if item.parent:
			pr_names.add(item.parent)

	for item in pi_items.values():
		if item.purchase_order:
			po_names.add(item.purchase_order)
		if item.purchase_receipt:
			pr_names.add(item.purchase_receipt)
		if item.parent:
			pi_names.add(item.parent)

	po_data = {}
	if po_names:
		res = frappe.get_all(
			"Purchase Order",
			filters={"name": ("in", list(po_names))},
			fields=["name", "transaction_date", "currency"]
		)
		po_data = {d.name: d for d in res}

	pr_data = {}
	if pr_names:
		res = frappe.get_all(
			"Purchase Receipt",
			filters={"name": ("in", list(pr_names))},
			fields=["name", "posting_date", "currency"]
		)
		pr_data = {d.name: d for d in res}

	pi_data = {}
	if pi_names:
		res = frappe.get_all(
			"Purchase Invoice",
			filters={"name": ("in", list(pi_names))},
			fields=["name", "posting_date", "currency"]
		)
		pi_data = {d.name: d for d in res}

	pi_by_pr = {}
	pi_date_by_pr = {}
	if pr_names:
		pi_items_res = frappe.get_all(
			"Purchase Invoice Item",
			filters={"purchase_receipt": ("in", list(pr_names)), "docstatus": 1},
			fields=["purchase_receipt", "parent", "item_code", "pr_detail"]
		)
		for d in pi_items_res:
			pi_by_pr[(d.purchase_receipt, d.item_code)] = d.parent
			pi_hdr = pi_data.get(d.parent)
			if pi_hdr:
				pi_date_by_pr[(d.purchase_receipt, d.item_code)] = pi_hdr.posting_date

	exchange_rates = frappe.get_all(
		"Currency Exchange",
		filters={"from_currency": "USD", "to_currency": "IDR"},
		fields=["name", "date", "exchange_rate"],
		order_by="date desc"
	)

	def get_usd_exchange_for_month_year(date_val):
		if not date_val:
			return None
		from frappe.utils import getdate
		d = getdate(date_val)
		rates_in_month = [
			r for r in exchange_rates 
			if getdate(r.date).year == d.year and getdate(r.date).month == d.month
		]
		if not rates_in_month:
			return None
		rates_on_or_before = [r for r in rates_in_month if getdate(r.date) <= d]
		match = rates_on_or_before[0] if rates_on_or_before else rates_in_month[0]
		return {"name": match.name, "exchange_rate": float(match.exchange_rate)}

	# Compute procurement info for all IN transactions
	procurement_info = {}
	for s in all_sles:
		if s.actual_qty > 0:
			info = {
				"voucher_no": s.voucher_no, "voucher_type": s.voucher_type,
				"posting_date": s.posting_date, "posting_time": s.posting_time,
				"purchase_order": None, "po_date": None,
				"purchase_receipt": None, "pr_date": None,
				"purchase_invoice": None, "pi_date": None,
				"vendor_currency": None, "vendor_rate": None,
				"idr_rate": None, "idr_amount": None,
				"usd_rate": None, "usd_amount": None,
				"currency_exchange_ref": None, "exchange_rate_value": None,
				"custom_sr_kode_lama": None, "custom_sr_no_rdo": None,
				"custom_sr_tanggal_rdo": None, "custom_sr_no_rio": None,
				"custom_sr_tanggal_rio": None, "custom_sr_transaction_type": None,
				"custom_sr_supplier_historis": None, "custom_sr_no_pib": None,
				"custom_sr_tahun_pib": None, "custom_sr_bulan_pib": None,
				"custom_sr_tanggal_pib": None, "custom_sr_kurs_pada_pib": None,
				"custom_sr_no_invoice_vendor": None, "custom_sr_tahun_doc_rdo": None,
				"custom_sr_qty_invoice": None, "custom_sr_supplier_currency": None,
				"custom_sr_harga_supplier": None, "custom_sr_total_dari_supplier": None,
				"custom_sr_kurs_ke_idr": None, "custom_sr_kurs_ke_usd": None,
				"custom_sr_total_in_usd": None
			}

			if not s.voucher_detail_no:
				procurement_info[s.name] = info
				continue

			if s.voucher_type == 'Purchase Receipt':
				item = pr_items.get(s.voucher_detail_no)
				if item:
					info["purchase_order"] = item.purchase_order
					po = po_data.get(item.purchase_order)
					if po:
						info["po_date"] = po.transaction_date
						info["vendor_currency"] = po.currency

					info["purchase_receipt"] = item.parent
					pr = pr_data.get(item.parent)
					if pr:
						info["pr_date"] = pr.posting_date
						if not info["vendor_currency"]:
							info["vendor_currency"] = pr.currency

					info["vendor_rate"] = item.rate
					info["idr_rate"] = item.base_rate
					info["idr_amount"] = item.base_amount
					info["purchase_invoice"] = pi_by_pr.get((item.parent, s.item_code))
					info["pi_date"] = pi_date_by_pr.get((item.parent, s.item_code))

			elif s.voucher_type == 'Purchase Invoice':
				item = pi_items.get(s.voucher_detail_no)
				if item:
					info["purchase_order"] = item.purchase_order
					po = po_data.get(item.purchase_order)
					if po:
						info["po_date"] = po.transaction_date
						info["vendor_currency"] = po.currency

					info["purchase_receipt"] = item.purchase_receipt
					pr = pr_data.get(item.purchase_receipt)
					if pr:
						info["pr_date"] = pr.posting_date
						if not info["vendor_currency"]:
							info["vendor_currency"] = pr.currency

					info["vendor_rate"] = item.rate
					info["idr_rate"] = item.base_rate
					info["idr_amount"] = item.base_amount
					info["purchase_invoice"] = item.parent
					pi = pi_data.get(item.parent)
					if pi:
						info["pi_date"] = pi.posting_date
						if not info["vendor_currency"]:
							info["vendor_currency"] = pi.currency

			elif s.voucher_type == 'Stock Reconciliation':
				# Map pre-fetched fields from the joined sri record
				info["custom_sr_kode_lama"] = s.get("custom_sr_kode_lama")
				info["custom_sr_no_rdo"] = s.get("custom_sr_no_rdo")
				info["custom_sr_tanggal_rdo"] = s.get("custom_sr_tanggal_rdo")
				info["custom_sr_no_rio"] = s.get("custom_sr_no_rio")
				info["custom_sr_tanggal_rio"] = s.get("custom_sr_tanggal_rio")
				info["custom_sr_transaction_type"] = s.get("custom_sr_transaction_type")
				info["custom_sr_supplier_historis"] = s.get("custom_sr_supplier_historis")
				info["custom_sr_no_pib"] = s.get("custom_sr_no_pib")
				info["custom_sr_tahun_pib"] = s.get("custom_sr_tahun_pib")
				info["custom_sr_bulan_pib"] = s.get("custom_sr_bulan_pib")
				info["custom_sr_tanggal_pib"] = s.get("custom_sr_tanggal_pib")
				info["custom_sr_kurs_pada_pib"] = s.get("custom_sr_kurs_pada_pib")
				info["custom_sr_no_invoice_vendor"] = s.get("custom_sr_no_invoice_vendor")
				info["custom_sr_tahun_doc_rdo"] = s.get("custom_sr_tahun_doc_rdo")
				info["custom_sr_qty_invoice"] = s.get("custom_sr_qty_invoice")
				info["custom_sr_supplier_currency"] = s.get("custom_sr_supplier_currency")
				info["custom_sr_harga_supplier"] = s.get("custom_sr_harga_supplier")
				info["custom_sr_total_dari_supplier"] = s.get("custom_sr_total_dari_supplier")
				info["custom_sr_kurs_ke_idr"] = s.get("custom_sr_kurs_ke_idr")
				info["custom_sr_kurs_ke_usd"] = s.get("custom_sr_kurs_ke_usd")
				info["custom_sr_total_in_usd"] = s.get("custom_sr_total_in_usd")
				pass

			if info["idr_rate"] is not None and s.voucher_type != 'Stock Reconciliation':
				if info["vendor_currency"] == 'USD':
					info["usd_rate"] = info["vendor_rate"]
					info["usd_amount"] = float(info["vendor_rate"] or 0.0) * float(s.actual_qty or 0.0)
					info["currency_exchange_ref"] = "Direct (Vendor USD)"
				else:
					timeline_date = info["pr_date"] or s.posting_date
					exchange_info = get_usd_exchange_for_month_year(timeline_date)
					if exchange_info:
						usd_to_idr_rate = exchange_info["exchange_rate"]
						info["usd_rate"] = float(info["idr_rate"]) / usd_to_idr_rate
						info["usd_amount"] = float(info["idr_amount"]) / usd_to_idr_rate if info["idr_amount"] is not None else None
						info["currency_exchange_ref"] = exchange_info["name"]
						info["exchange_rate_value"] = usd_to_idr_rate
					else:
						info["usd_rate"] = "No Currency Exchange"
						info["usd_amount"] = "No Currency Exchange"
						info["currency_exchange_ref"] = "No Currency Exchange"

			procurement_info[s.name] = info

	# Simulate FIFO
	fifo_queues = {}
	out_splits = {}
	opening_fifo_queues = {}

	from_date_obj = get_datetime(filters.from_date + " 00:00:00") if filters.get("from_date") else None
	captured_opening = False

	for s in all_sles:
		if from_date_obj and not captured_opening and s.posting_datetime >= from_date_obj:
			import copy
			opening_fifo_queues = copy.deepcopy(fifo_queues)
			captured_opening = True

		key = (s.item_code, s.warehouse)
		if key not in fifo_queues:
			fifo_queues[key] = []

		if s.actual_qty > 0:
			info = procurement_info.get(s.name, {}).copy()
			fifo_queues[key].append({"qty": s.actual_qty, "rate": flt(s.valuation_rate) or flt(s.incoming_rate), "procurement": info})

		elif s.actual_qty < 0:
			qty_to_consume = abs(s.actual_qty)
			consumed_pieces = []

			while qty_to_consume > 0 and fifo_queues[key]:
				batch = fifo_queues[key][0]
				if batch["qty"] <= qty_to_consume:
					consumed_pieces.append({
						"qty": -batch["qty"],
						"procurement": dict(batch["procurement"])
					})
					qty_to_consume -= batch["qty"]
					fifo_queues[key].pop(0)
				else:
					consumed_pieces.append({
						"qty": -qty_to_consume,
						"procurement": dict(batch["procurement"])
					})
					batch["qty"] -= qty_to_consume
					qty_to_consume = 0

			if qty_to_consume > 0:
				consumed_pieces.append({
					"qty": -qty_to_consume,
					"procurement": {}
				})
			
			out_splits[s.name] = consumed_pieces

	# Apply splits to reported sl_entries
	new_sl_entries = []
	for sle in sl_entries:
		if sle.actual_qty > 0:
			info = procurement_info.get(sle.name, {})
			sle.update(info)
			new_sl_entries.append(sle)

		elif sle.actual_qty < 0:
			splits = out_splits.get(sle.name, [])
			if not splits:
				new_sl_entries.append(sle)
			else:
				for split in splits:
					new_sle = sle.copy()
					new_sle.actual_qty = split["qty"]
					new_sle.update(split["procurement"])
					
					# proportionally adjust stock_value_difference and idr_amount / usd_amount
					ratio = split["qty"] / sle.actual_qty if sle.actual_qty else 1
					if new_sle.get("stock_value_difference"):
						new_sle.stock_value_difference = new_sle.stock_value_difference * ratio
					
					if new_sle.get("idr_rate") is not None:
						new_sle.idr_amount = float(new_sle.idr_rate) * abs(new_sle.actual_qty)
					if new_sle.get("usd_rate") and isinstance(new_sle.get("usd_rate"), (int, float)):
						new_sle.usd_amount = float(new_sle.usd_rate) * abs(new_sle.actual_qty)

					new_sl_entries.append(new_sle)
		else:
			new_sl_entries.append(sle)

	if from_date_obj and not captured_opening:
		import copy
		opening_fifo_queues = copy.deepcopy(fifo_queues)

	return new_sl_entries, opening_fifo_queues


def convert_to_tree_view(data, item_details, filters, opening_fifo_queues):
	tree_data = []
	
	# Group transactions by item
	transactions_by_item = defaultdict(list)
	generic_opening_by_item = {}
	
	for row in data:
		item_code = row.get("item_code")
		if item_code in ["'Opening'", _("'Opening'")]:
			single_item = filters.get("item_code")
			if single_item:
				generic_opening_by_item[single_item] = row
		else:
			if item_code:
				transactions_by_item[item_code].append(row)
				
	all_items = set(transactions_by_item.keys()).union(set(generic_opening_by_item.keys()))
	
	if opening_fifo_queues:
		for (q_item, q_warehouse), pieces in opening_fifo_queues.items():
			if filters.get("warehouse") and q_warehouse != filters.get("warehouse"):
				continue
			if pieces:
				all_items.add(q_item)
	
	for item_code in all_items:
		txs = transactions_by_item.get(item_code, [])
		
		item_info = item_details.get(item_code)
		if not item_info:
			res = frappe.db.get_value("Item", item_code, ["item_name", "stock_uom"], as_dict=True)
			item_info = res or frappe._dict({"item_name": item_code, "stock_uom": ""})
			
		item_name = item_info.get("item_name", item_code)
		
		# Calculate opening balance
		generic_op = generic_opening_by_item.get(item_code)
		if generic_op:
			opening_qty = flt(generic_op.get("qty_after_transaction", 0))
			opening_value = flt(generic_op.get("stock_value", 0))
			opening_rate = flt(generic_op.get("valuation_rate", 0))
		elif txs:
			first_tx = txs[0]
			opening_qty = flt(first_tx.get("qty_after_transaction", 0)) - flt(first_tx.get("actual_qty", 0))
			opening_value = flt(first_tx.get("stock_value", 0)) - flt(first_tx.get("stock_value_difference", 0))
			opening_rate = flt(opening_value / opening_qty) if opening_qty else 0.0
		else:
			from erpnext.stock.stock_ledger import get_previous_sle
			
			last_entry = get_previous_sle({
				"item_code": item_code,
				"warehouse_condition": get_warehouse_condition(filters.get("warehouse")) if filters.get("warehouse") else "",
				"posting_date": filters.get("from_date"),
				"posting_time": "00:00:00"
			}) or {}
			
			opening_qty = flt(last_entry.get("qty_after_transaction", 0))
			opening_value = flt(last_entry.get("stock_value", 0))
			opening_rate = flt(last_entry.get("valuation_rate", 0))
			
		# Calculate closing balance
		if txs:
			last_tx = txs[-1]
			closing_qty = flt(last_tx.get("qty_after_transaction", 0))
			closing_value = flt(last_tx.get("stock_value", 0))
			closing_rate = flt(last_tx.get("valuation_rate", 0))
		else:
			closing_qty = opening_qty
			closing_value = opening_value
			closing_rate = opening_rate
		
		# 1. Parent Item Row
		p_row = frappe._dict({
			"indent_name": f"{item_code}_parent",
			"parent_row": None,
			"indent": 0,
			"date": f"[{item_code}] {item_name}",
			"item_code": item_code,
			"item_name": item_name,
			"stock_uom": item_info.get("stock_uom"),
			"qty_after_transaction": closing_qty,
			"stock_value": closing_value,
			"usd_currency": "USD",
		})
		tree_data.append(p_row)
		
		# 2. Opening Balance Row
		op_row = frappe._dict({
			"indent_name": f"{item_code}_opening",
			"parent_row": f"{item_code}_parent",
			"indent": 1,
			"date": _("Opening Balance"),
			"qty_after_transaction": opening_qty,
			"valuation_rate": opening_rate,
			"stock_value": opening_value,
			"usd_currency": "USD",
		})
		tree_data.append(op_row)
		
		# 2a. Opening Details (FIFO pieces)
		item_opening_pieces = []
		for (q_item, q_warehouse), pieces in opening_fifo_queues.items():
			if q_item == item_code:
				if filters.get("warehouse") and q_warehouse != filters.get("warehouse"):
					continue
				item_opening_pieces.extend(pieces)
		
		if item_opening_pieces:
			for idx, piece in enumerate(item_opening_pieces):
				qty = piece.get("qty", 0)
				rate = piece.get("rate", 0)
				proc = piece.get("procurement", {})
				piece_row = frappe._dict({
					"indent_name": f"{item_code}_opening_detail_{idx}",
					"parent_row": f"{item_code}_opening",
					"indent": 2,
					"in_qty": qty,
					"incoming_rate": rate,
					"valuation_rate": rate,
					"stock_value": qty * rate,
					"usd_currency": "USD",
				})
				piece_row.update(proc)
				
				voucher_ref = proc.get("voucher_no") or proc.get("purchase_receipt") or proc.get("purchase_invoice") or proc.get("purchase_order") or _("Previous Receipt")
				piece_row["date"] = f"{_('Sisa dari')} {voucher_ref}"
				tree_data.append(piece_row)
		
		# 3. Transactions Progress Group
		if txs:
			tx_hdr = frappe._dict({
				"indent_name": f"{item_code}_progress_header",
				"parent_row": f"{item_code}_parent",
				"indent": 1,
				"date": _("Transactions Progress"),
				"usd_currency": "USD",
			})
			tree_data.append(tx_hdr)
			
			for idx, tx in enumerate(txs):
				tx_row = copy.deepcopy(tx)
				tx_row.update({
					"indent_name": f"{item_code}_progress_tx_{idx}",
					"parent_row": f"{item_code}_progress_header",
					"indent": 2,
					"usd_currency": "USD",
				})
				tree_data.append(tx_row)
				
		# 4. Closing Balance Row
		cl_row = frappe._dict({
			"indent_name": f"{item_code}_closing",
			"parent_row": f"{item_code}_parent",
			"indent": 1,
			"date": _("Closing Balance"),
			"qty_after_transaction": closing_qty,
			"valuation_rate": closing_rate,
			"stock_value": closing_value,
			"usd_currency": "USD",
		})
		tree_data.append(cl_row)
		
	return tree_data

def get_parent_item_row(item_code, item_details, qty, val):
	item_info = item_details.get(item_code)
	if not item_info:
		item_info = frappe.db.get_value("Item", item_code, ["item_name", "stock_uom"], as_dict=True) or frappe._dict({"item_name": item_code, "stock_uom": ""})
	return frappe._dict({
		"indent_name": f"{item_code}_parent",
		"parent_row": None,
		"indent": 0,
		"item_code": item_code,
		"item_name": item_info.get("item_name", item_code),
		"stock_uom": item_info.get("stock_uom"),
		"qty_after_transaction": qty,
		"stock_value": val,
		"usd_currency": "USD",
	})

def get_balance_row(item_code, label, qty, rate, val, is_opening=True):
	suffix = "opening" if is_opening else "closing"
	return frappe._dict({
		"indent_name": f"{item_code}_{suffix}",
		"parent_row": f"{item_code}_parent",
		"indent": 1,
		"date": label,
		"qty_after_transaction": qty,
		"valuation_rate": rate,
		"stock_value": val,
		"usd_currency": "USD",
	})

