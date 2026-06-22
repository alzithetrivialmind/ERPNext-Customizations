# ==========================================
# SERVER SCRIPT
# Script Type        : Document Event
# Reference DocType  : Sales Invoice
# DocType Event      : Before Validate
# ==========================================

for item in doc.items:
    # 1. Initialize custom_user_rate if empty
    if not item.get("custom_user_rate") and item.get("item_code"):
        item.custom_user_rate = item.get("price_list_rate") or item.get("rate") or 0.0

    baseline = flt(item.get("custom_user_rate"))
    dtype    = item.get("custom_user_discount_type")
    dval     = flt(item.get("custom_user_discount_value"))
    qty      = flt(item.get("qty")) or 1.0

    # 2. Calculate discount
    # - Percentage : same % per unit  (e.g. 10% off each unit)
    # - Amount     : total row discount, divided by qty to get per-unit value
    #                (e.g. $300 total on 5 pcs = $60 discount per unit)
    if dtype == "Percentage":
        discount_amt = baseline * (dval / 100.0)
    elif dtype == "Amount":
        discount_amt = dval / qty
    else:
        discount_amt = 0.0

    final_rate = baseline - discount_amt

    # Guard: rate cannot go below zero
    if final_rate < 0:
        final_rate   = 0.0
        discount_amt = baseline

    # 3. Sync to standard ERPNext fields
    # ERPNext's calculate_taxes_and_totals will use these values automatically
    conversion_rate = flt(doc.get("conversion_rate")) or 1.0

    item.price_list_rate = baseline
    if hasattr(item, "base_price_list_rate"):
        item.base_price_list_rate = baseline * conversion_rate

    item.discount_amount = discount_amt
    if hasattr(item, "base_discount_amount"):
        item.base_discount_amount = discount_amt * conversion_rate

    item.discount_percentage = (discount_amt / baseline * 100.0) if baseline != 0 else 0.0

    item.rate = final_rate
    if hasattr(item, "base_rate"):
        item.base_rate = final_rate * conversion_rate
