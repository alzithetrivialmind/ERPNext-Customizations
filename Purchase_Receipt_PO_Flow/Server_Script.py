# ==========================================
# SERVER SCRIPT
# Script Type: Document Event
# Reference DocType: Purchase Receipt
# DocType Event: Before Save
# ==========================================

if not doc.items or len(doc.items) == 0:
    frappe.throw("Purchase Receipt must contain at least 1 item.")

for d in doc.items:
    if not d.get("purchase_order"):
        frappe.throw(f"Item {d.item_code or ''} is not linked to a Purchase Order.")
    if not d.get("purchase_order_item"):
        frappe.throw(f"Item {d.item_code or ''} is not linked to a Purchase Order row (Purchase Order Item).")
