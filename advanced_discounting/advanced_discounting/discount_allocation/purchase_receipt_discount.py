# Copyright (c) 2026, Palma Progress Shipyard and contributors
# For license information, please see license.txt

"""
Module 1 — PO → Purchase Receipt Proportional Discount Allocation

Hooked via doc_events in hooks.py:
    Purchase Receipt → validate   → validate()
    Purchase Receipt → on_cancel  → on_cancel()

This module performs two tasks sequentially inside validate():
  1. Legacy base-rate sync (migrated from discount_fix/Purchase_Receipt/Server_Script.py)
     — resolves custom_palma_base_rate ↔ price_list_rate for all items.
  2. Proportional discount allocation for discount-eligible PO items
     — writes to the standard `discount_amount` field on PR Item so that
       ERPNext's stock valuation uses the discounted rate.
"""

import frappe
from frappe.utils import flt


# ═══════════════════════════════════════════════════════════════════
#  HOOK: Purchase Receipt → validate
# ═══════════════════════════════════════════════════════════════════

def validate(doc, method):
    """Entry point for Purchase Receipt validate event.

    Execution order:
      1. Historical entry guard (skip everything if importing / historical)
      2. Legacy base-rate sync (for ALL items — Module 2 compatibility)
      3. Proportional discount allocation (for discount-eligible items only)
    """
    # ── HISTORICAL ENTRY GUARD ──
    if frappe.flags.in_import or doc.get("custom_disc_is_historical"):
        # Trust all values as-is.  Do NOT recalculate, log, or overwrite.
        return

    # Step 1: Legacy base-rate sync (Module 2 migrated logic)
    _sync_base_rates(doc)

    # Step 2: Proportional discount allocation (Module 1 core logic)
    _allocate_discounts(doc)


# ═══════════════════════════════════════════════════════════════════
#  HOOK: Purchase Receipt → on_cancel
# ═══════════════════════════════════════════════════════════════════

def on_cancel(doc, method):
    """On cancel, ERPNext automatically reverses the stock entry
    (including the valuation rate).  The allocation log rows remain
    as historical record.  No manual reversal writes needed."""
    pass


# ═══════════════════════════════════════════════════════════════════
#  STEP 1: Legacy Base-Rate Sync
#  (ported from discount_fix/Purchase_Receipt/Server_Script.py)
# ═══════════════════════════════════════════════════════════════════

def _sync_base_rates(doc):
    """Ensure custom_palma_base_rate ↔ price_list_rate are in sync,
    and compute row-level discount from the Palma custom fields.

    This runs for ALL items, regardless of discount eligibility.
    For eligible items, the discount_amount computed here will be
    OVERWRITTEN by step 2 (_allocate_discounts).
    """
    conversion_rate = flt(doc.get("conversion_rate") or 1) or 1.0

    for item in doc.items:
        baseline = flt(item.get("custom_palma_base_rate"))

        # Robust fallback chain
        if baseline <= 0:
            baseline = flt(item.get("price_list_rate"))
        if baseline <= 0:
            baseline = flt(item.get("rate"))

        # Sync back
        item.custom_palma_base_rate = baseline

        dtype = item.get("custom_palma_discount_type")
        dval = flt(item.get("custom_palma_discount_amount"))
        qty = flt(item.get("qty") or 1) or 1.0

        if dtype == "Percentage":
            discount_amt = baseline * (dval / 100.0)
        elif dtype == "Amount":
            discount_amt = dval / qty
        else:
            discount_amt = 0.0

        final_rate = baseline - discount_amt
        if final_rate < 0:
            final_rate = 0.0
            discount_amt = baseline

        # Write to standard ERPNext fields
        item.price_list_rate = baseline
        if item.meta.has_field("base_price_list_rate"):
            item.base_price_list_rate = baseline * conversion_rate

        item.discount_amount = discount_amt
        if item.meta.has_field("base_discount_amount"):
            item.base_discount_amount = discount_amt * conversion_rate

        item.discount_percentage = (
            (discount_amt / baseline * 100.0) if baseline > 0 else 0.0
        )

        item.rate = final_rate
        if item.meta.has_field("base_rate"):
            item.base_rate = final_rate * conversion_rate


# ═══════════════════════════════════════════════════════════════════
#  STEP 2: Proportional Discount Allocation
# ═══════════════════════════════════════════════════════════════════

def _allocate_discounts(doc):
    """For items linked to a PO with discount-eligible rows, calculate
    and write proportional discount allocation.

    Writes to:
      - Standard `discount_amount` on PR Item  (affects valuation rate)
      - Standard `rate` on PR Item
      - Standard `discount_percentage` on PR Item
      - Custom `custom_disc_allocated_discount` (audit/display)
      - Custom `custom_disc_allocation_log` child table on PR parent
    """
    # Clear stale allocation log rows from previous saves
    doc.set("custom_disc_allocation_log", [])

    conversion_rate = flt(doc.get("conversion_rate") or 1) or 1.0

    # Group PR items by their source Purchase Order
    po_groups = {}  # { po_name: [pr_item_rows] }
    for item in doc.items:
        po_name = item.get("purchase_order")
        po_item_name = item.get("purchase_order_item")
        if not po_name or not po_item_name:
            continue
        po_groups.setdefault(po_name, []).append(item)

    # Process each PO group independently
    for po_name, pr_items in po_groups.items():
        po_doc = frappe.get_doc("Purchase Order", po_name)

        # Identify eligible PO items & compute discount pool
        eligible_po_items = [
            poi for poi in po_doc.items if poi.get("custom_disc_eligible")
        ]
        if not eligible_po_items:
            continue

        # Q2: sum native discount_amount from eligible PO Item rows
        # discount_amount on PO Item is per-unit; multiply by qty for total
        po_discount_pool = sum(
            flt(poi.discount_amount) * flt(poi.qty)
            for poi in eligible_po_items
        )

        # Total undiscounted amount for eligible items
        po_eligible_total = sum(
            flt(poi.qty) * flt(poi.price_list_rate)
            for poi in eligible_po_items
        )

        if po_eligible_total <= 0 or po_discount_pool <= 0:
            continue

        # Build a lookup: po_item.name → po_item doc
        poi_map = {poi.name: poi for poi in eligible_po_items}

        # Filter PR items to only eligible ones (their PO item has the flag)
        for pr_item in pr_items:
            po_item_row = poi_map.get(pr_item.purchase_order_item)
            if not po_item_row:
                # This PR item's PO row is not discount-eligible; skip
                continue

            # ── Per-PO-item discount slice ──
            poi_amount = flt(po_item_row.qty) * flt(po_item_row.price_list_rate)
            if poi_amount <= 0:
                continue

            poi_discount_share = po_discount_pool * (poi_amount / po_eligible_total)

            # ── Previously allocated for this PO item across other PRs ──
            already_allocated = _get_previously_allocated(
                po_name, pr_item.purchase_order_item, exclude_pr=doc.name
            )

            # ── Remaining qty ──
            total_received = _get_total_received_qty(
                po_name, pr_item.purchase_order_item, exclude_pr=doc.name
            )
            remaining_qty = flt(po_item_row.qty) - total_received

            # ── Proportional or remainder? ──
            is_closing = remaining_qty <= flt(pr_item.qty)

            if is_closing:
                # Closing receipt: absorb exact remainder (prevents FP drift)
                allocated = poi_discount_share - already_allocated
                alloc_method = "remainder"
            else:
                # Proportional: (pr_qty / po_qty) × poi_discount_share
                allocated = poi_discount_share * (
                    flt(pr_item.qty) / flt(po_item_row.qty)
                )
                alloc_method = "proportional"

            allocated = flt(allocated, 2)  # round to 2 decimal places

            # ── Write to STANDARD fields (affects valuation) ──
            per_unit_discount = flt(allocated / (flt(pr_item.qty) or 1), 2)
            pr_item.discount_amount = per_unit_discount

            if flt(pr_item.price_list_rate) > 0:
                pr_item.discount_percentage = flt(
                    per_unit_discount / pr_item.price_list_rate * 100.0, 2
                )
            else:
                pr_item.discount_percentage = 0.0

            pr_item.rate = flt(pr_item.price_list_rate) - per_unit_discount

            if pr_item.meta.has_field("base_rate"):
                pr_item.base_rate = pr_item.rate * conversion_rate
            if pr_item.meta.has_field("base_discount_amount"):
                pr_item.base_discount_amount = per_unit_discount * conversion_rate

            # ── Write to CUSTOM audit field ──
            pr_item.custom_disc_allocated_discount = allocated

            # ── Append log entry (flat on PR parent) ──
            doc.append("custom_disc_allocation_log", {
                "purchase_receipt_item": pr_item.name,
                "item_code": pr_item.item_code,
                "purchase_order": po_name,
                "purchase_order_item": pr_item.purchase_order_item,
                "po_eligible_total": po_eligible_total,
                "po_discount_pool": po_discount_pool,
                "pr_row_amount": flt(pr_item.qty) * flt(pr_item.price_list_rate),
                "allocated_discount": allocated,
                "allocation_method": alloc_method,
                "is_closing_receipt": 1 if is_closing else 0,
            })


# ═══════════════════════════════════════════════════════════════════
#  HELPER QUERIES
# ═══════════════════════════════════════════════════════════════════

def _get_previously_allocated(po_name, po_item_name, exclude_pr):
    """Sum custom_disc_allocated_discount from all *submitted* PR Items
    that reference this PO item, excluding the current PR."""
    result = frappe.db.sql(
        """
        SELECT COALESCE(SUM(pri.custom_disc_allocated_discount), 0)
        FROM `tabPurchase Receipt Item` pri
        JOIN `tabPurchase Receipt` pr ON pr.name = pri.parent
        WHERE pri.purchase_order = %s
          AND pri.purchase_order_item = %s
          AND pr.docstatus = 1
          AND pr.name != %s
        """,
        (po_name, po_item_name, exclude_pr),
    )
    return flt(result[0][0]) if result else 0.0


def _get_total_received_qty(po_name, po_item_name, exclude_pr):
    """Sum qty from all *submitted* PR Items for this PO item,
    excluding the current PR."""
    result = frappe.db.sql(
        """
        SELECT COALESCE(SUM(pri.qty), 0)
        FROM `tabPurchase Receipt Item` pri
        JOIN `tabPurchase Receipt` pr ON pr.name = pri.parent
        WHERE pri.purchase_order = %s
          AND pri.purchase_order_item = %s
          AND pr.docstatus = 1
          AND pr.name != %s
        """,
        (po_name, po_item_name, exclude_pr),
    )
    return flt(result[0][0]) if result else 0.0
