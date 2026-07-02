# Copyright (c) 2026, PT Palma Progress Shipyard and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt
import copy
from collections import defaultdict
from .queries import get_warehouse_condition

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
	
	# Pre-fetch item names to sort by item_name
	item_names = {}
	for item_code in all_items:
		info = item_details.get(item_code)
		if not info:
			res = frappe.db.get_value("Item", item_code, ["item_name", "stock_uom"], as_dict=True)
			info = res or frappe._dict({"item_name": item_code, "stock_uom": ""})
			item_details[item_code] = info
		item_names[item_code] = info.get("item_name", item_code)
		
	# Sort items alphabetically by item_name so output is deterministic and matches user request
	sorted_items = sorted(all_items, key=lambda k: item_names[k])
	
	for item_code in sorted_items:
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
			"sort_order": f"{item_code}_0_0000",
			"date": f"[{item_code}] {item_name}",
			"item_code": item_code,
			"item_name": item_name,
			"stock_uom": item_info.get("stock_uom"),
			"qty_after_transaction": closing_qty,
			"valuation_rate": closing_rate,
			"in_out_rate": closing_rate,
			"stock_value": closing_value,
			"usd_currency": "USD",
		})
		tree_data.append(p_row)
		
		# 2. Opening Balance Row
		op_row = frappe._dict({
			"indent_name": f"{item_code}_opening",
			"parent_row": f"{item_code}_parent",
			"indent": 1,
			"sort_order": f"{item_code}_1_0000",
			"date": _("Opening Balance"),
			"qty_after_transaction": opening_qty,
			"valuation_rate": opening_rate,
			"in_out_rate": opening_rate,
			"stock_value": opening_value,
			"usd_currency": "USD",
		})
		tree_data.append(op_row)
		
		# 2a. Opening Details (FIFO pieces) — displayed as "remaining stock", not "incoming"
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
					"sort_order": f"{item_code}_1_{str(idx + 1).zfill(4)}",
					# Show as remaining balance, not as incoming transaction
					"qty_after_transaction": qty,
					"valuation_rate": rate,
					"in_out_rate": rate,
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
				"sort_order": f"{item_code}_2_0000",
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
					"sort_order": f"{item_code}_2_{str(idx + 1).zfill(4)}",
					"usd_currency": "USD",
				})
				tree_data.append(tx_row)
				
		# 4. Closing Balance Row
		cl_row = frappe._dict({
			"indent_name": f"{item_code}_closing",
			"parent_row": f"{item_code}_parent",
			"indent": 1,
			"sort_order": f"{item_code}_3_0000",
			"date": _("Closing Balance"),
			"qty_after_transaction": closing_qty,
			"valuation_rate": closing_rate,
			"in_out_rate": closing_rate,
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
