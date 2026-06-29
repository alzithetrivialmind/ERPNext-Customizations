# ==========================================
# SERVER SCRIPT
# Script Type        : Document Event
# Reference DocType  : Purchase Order
# DocType Event      : Before Validate
# ==========================================
#
# SYNC LOGIC:
#   custom_custom_base_rate is the "source of truth" for the user-visible base price.
#   It is kept in 2-way sync with price_list_rate by the Client Script on the browser side.
#   The Server Script (this file) is the authoritative fallback that runs on every save/submit
#   to guarantee correctness even when the client-side sync doesn't fire (e.g., data import,
#   API submissions, or race conditions on save).
#
# FALLBACK CHAIN for baseline:
#   1. custom_custom_base_rate  (user-entered or synced from price_list_rate)
#   2. price_list_rate          (ERPNext's own fetched rate from the price list)
#   3. rate                     (whatever ERPNext already computed)
# ==========================================

for item in doc.items:
    baseline = float(item.get("custom_custom_base_rate") or 0.0)

    # Robust fallback: if custom_custom_base_rate is still 0, read from ERPNext fields
    if baseline <= 0.0:
        baseline = float(item.get("price_list_rate") or 0.0)
    if baseline <= 0.0:
        baseline = float(item.get("rate") or 0.0)

    # Sync back: always keep custom_custom_base_rate in line with the resolved baseline
    item.custom_custom_base_rate = baseline

    dtype = item.get("custom_custom_discount_type")
    dval  = float(item.get("custom_new_custom_discount") or 0.0)
    qty   = float(item.get("qty") or 1.0) or 1.0

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

    conversion_rate = float(doc.get("conversion_rate") or 1.0) or 1.0

    # Sync price_list_rate ↔ custom_custom_base_rate (server side ensures both are in sync)
    item.price_list_rate = baseline
    if item.meta.has_field("base_price_list_rate"):
        item.base_price_list_rate = baseline * conversion_rate

    item.discount_amount = discount_amt
    if item.meta.has_field("base_discount_amount"):
        item.base_discount_amount = discount_amt * conversion_rate

    item.discount_percentage = (discount_amt / baseline * 100.0) if baseline > 0 else 0.0

    item.rate = final_rate
    if item.meta.has_field("base_rate"):
        item.base_rate = final_rate * conversion_rate
