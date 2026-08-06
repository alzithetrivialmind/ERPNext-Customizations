# ==========================================
# SERVER SCRIPT
# Script Type: Document Event
# Reference DocType: Purchase Receipt
# DocType Event: Before Validate
# ==========================================

if not doc.items or len(doc.items) == 0:
    frappe.throw("Purchase Receipt must contain at least 1 item.")

po_name = None
for d in doc.items:
    if not d.get("purchase_order"):
        frappe.throw(f"Item {d.item_code or ''} is not linked to a Purchase Order.")
    if not d.get("purchase_order_item"):
        frappe.throw(f"Item {d.item_code or ''} is not linked to a Purchase Order row (Purchase Order Item).")
    
    if not po_name:
        po_name = d.get("purchase_order")

# FORCE SYNC CURRENCY FROM PO
# This fixes the ERPNext core issue where the server resets the document 
# currency to the Supplier's default (IDR) before validation, causing multi-currency errors.
if po_name:
    po = frappe.get_doc("Purchase Order", po_name)
    if po.currency != doc.currency:
        doc.currency = po.currency
        doc.buying_price_list = po.buying_price_list
        doc.price_list_currency = po.price_list_currency
        doc.conversion_rate = po.conversion_rate
        doc.plc_conversion_rate = po.plc_conversion_rate
