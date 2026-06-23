# ==========================================
# SERVER SCRIPT
# Script Type        : Document Event
# Reference DocType  : Purchase Receipt
# DocType Event      : Before Validate
# NOTE               : Only install this script if your business
#                      receives goods WITHOUT a Purchase Order first.
#                      If your workflow is always PO → PR, the discount
#                      is already carried over automatically from the PO
#                      and this script is not needed.
# ==========================================

for item in doc.items:
    if not item.get("custom_custom_base_rate") and item.get("item_code"):
        item.custom_custom_base_rate = item.get("price_list_rate") or item.get("rate") or 0.0

    baseline = flt(item.get("custom_custom_base_rate"))
    dtype    = item.get("custom_custom_discount_type")
    dval     = flt(item.get("custom_new_custom_discount"))
    qty      = flt(item.get("qty")) or 1.0

    if dtype == "Percentage":
        discount_amt = baseline * (dval / 100.0)
    elif dtype == "Amount":
        discount_amt = dval / qty
    else:
        discount_amt = 0.0

    final_rate = baseline - discount_amt

    if final_rate < 0:
        final_rate   = 0.0
        discount_amt = baseline

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
