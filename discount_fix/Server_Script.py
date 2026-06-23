# ==========================================
# SERVER SCRIPT (UI ERPNext)
# Script Type: Document Event
# Reference Document Type: Sales Invoice (atau PO, SO, dll)
# DocType Event: Before Validate
# ==========================================

for item in doc.items:
    # 1. Initialize custom_custom_base_rate only if completely empty AND item_code exists
    if not item.get("custom_custom_base_rate") and item.get("item_code"):
        item.custom_custom_base_rate = item.get("price_list_rate") or item.get("rate") or 0.0

    baseline = flt(item.get("custom_custom_base_rate"))
    dtype    = item.get("custom_custom_discount_type")
    dval     = flt(item.get("custom_new_custom_discount"))
    qty      = flt(item.get("qty")) or 1.0

    # 2. Calculate discount
    # - Percentage: discount is applied per unit (e.g. 10% off each unit)
    # - Amount: the input value is treated as a TOTAL discount for the entire row,
    #           so we divide by qty to get the per-unit discount.
    #           Example: input $100 discount on 10 pcs = $10 discount per unit.
    if dtype == "Percentage":
        discount_amt = baseline * (dval / 100.0)

    elif dtype == "Amount":
        # BUG FIX: treat dval as total row discount, divide by qty for per-unit value
        discount_amt = dval / qty

    else:
        discount_amt = 0.0

    final_rate = baseline - discount_amt

    # Guard against negative rate
    if final_rate < 0:
        final_rate = 0.0
        discount_amt = baseline

    # 3. Synchronize standard ERPNext fields
    # By overwriting these fields at "Before Validate" stage,
    # ERPNext's built-in "calculate_taxes_and_totals" will process them smoothly.
    item.price_list_rate = baseline

    conversion_rate = flt(doc.get("conversion_rate")) or 1.0
    if hasattr(item, "base_price_list_rate"):
        item.base_price_list_rate = baseline * conversion_rate

    item.discount_amount = discount_amt
    if hasattr(item, "base_discount_amount"):
        item.base_discount_amount = discount_amt * conversion_rate

    if baseline != 0:
        item.discount_percentage = (discount_amt / baseline) * 100.0
    else:
        item.discount_percentage = 0.0

    item.rate = final_rate
    if hasattr(item, "base_rate"):
        item.base_rate = final_rate * conversion_rate
