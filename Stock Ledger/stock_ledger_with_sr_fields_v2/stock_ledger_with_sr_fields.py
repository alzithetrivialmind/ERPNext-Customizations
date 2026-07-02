# Copyright (c) 2026, PT Palma Progress Shipyard and contributors
# For license information, please see license.txt

import frappe
import copy
from frappe import _
from frappe.utils import cint, flt
from erpnext.stock.doctype.serial_no.serial_no import get_serial_nos
from erpnext.stock.doctype.stock_reconciliation.stock_reconciliation import get_stock_balance_for
from erpnext.stock.utils import is_reposting_item_valuation_in_progress, update_included_uom_in_report

# Import local modular files
from .columns import get_columns
from .queries import (
	get_stock_ledger_entries,
	get_items,
	get_item_details,
	get_opening_balance_from_batch,
	get_opening_balance,
	check_inventory_dimension_filters_applied
)
from .procurement import enrich_sl_entries_with_procurement_details
from .tree_view import convert_to_tree_view

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
