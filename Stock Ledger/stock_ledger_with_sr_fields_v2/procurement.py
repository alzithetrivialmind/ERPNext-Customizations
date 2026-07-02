# Copyright (c) 2026, PT Palma Progress Shipyard and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import get_datetime, flt

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
