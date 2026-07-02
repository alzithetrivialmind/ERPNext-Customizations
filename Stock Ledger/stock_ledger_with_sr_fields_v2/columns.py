# Copyright (c) 2026, PT Palma Progress Shipyard and contributors
# For license information, please see license.txt

from frappe import _
from erpnext.stock.doctype.inventory_dimension.inventory_dimension import get_inventory_dimensions

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

	# Hidden column for tree view sort stability
	columns.append(
		{"label": _("Sort Order"), "fieldname": "sort_order", "fieldtype": "Data", "width": 0, "hidden": 1}
	)

	return columns
