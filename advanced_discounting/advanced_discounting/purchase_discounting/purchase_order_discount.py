# Copyright (c) 2026, Palma Progress Shipyard and contributors
# For license information, please see license.txt

"""
Module 2 — Purchase Order Row & Global Discount (server-side fallback)

Hooked via doc_events in hooks.py:
    Purchase Order → before_validate → before_validate()
"""

from frappe.utils import flt


def before_validate(doc, method):
    """Authoritative server-side discount calculation for Purchase Order."""
    conversion_rate = flt(doc.get("conversion_rate") or 1) or 1.0

    for item in doc.items:
        baseline = flt(item.get("custom_palma_base_rate"))

        if baseline <= 0:
            baseline = flt(item.get("price_list_rate"))
        if baseline <= 0:
            baseline = flt(item.get("rate"))

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
