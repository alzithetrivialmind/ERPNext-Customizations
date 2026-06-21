# ==========================================
# SERVER SCRIPT (UI ERPNext)
# Script Type: Document Event
# Reference Document Type: Sales Invoice (atau PO, SO, dll)
# DocType Event: Before Validate
# ==========================================

for item in doc.items:
    # 1. Initialize custom_user_rate only if completely empty AND item_code exists
    if not item.get("custom_user_rate") and item.get("item_code"):
        item.custom_user_rate = item.get("price_list_rate") or item.get("rate") or 0.0

    baseline = flt(item.get("custom_user_rate"))
    dtype = item.get("custom_user_discount_type")
    dval = flt(item.get("custom_user_discount_value"))

    # 2. Calculate pure row-level discount
    if dtype == "Percentage":
        discount_amt = baseline * (dval / 100.0)
    elif dtype == "Amount":
        discount_amt = dval
    else:
        discount_amt = 0.0

    final_rate = baseline - discount_amt

    # 3. Synchronize standard fields
    # Dengan menimpa field standar di tahap "Before Validate", 
    # proses "calculate_taxes_and_totals" bawaan ERPNext akan memprosesnya dengan mulus
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
