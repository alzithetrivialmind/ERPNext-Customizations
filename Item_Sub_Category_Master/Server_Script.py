# ==========================================
# SERVER SCRIPT
# Script Type: Document Event
# Reference DocType: Item Sub Category Master
# DocType Event: Before Insert (or Before Save)
# ==========================================

def execute(doc, method):
    if not doc.subcategory_code:
        # Get last sequence for this letter prefix under this category
        last_record = frappe.db.sql("""
            SELECT MAX(CAST(SUBSTRING(subcategory_code, 2) AS UNSIGNED)) as max_seq
            FROM `tabItem Sub Category Master` 
            WHERE parent_category = %s AND letter_prefix = %s
        """, (doc.parent_category, doc.letter_prefix))
        
        # Calculate next sequence
        if last_record and last_record[0][0]:
            next_seq = last_record[0][0] + 1
        else:
            next_seq = 1
            
        # Generate subcategory_code: D001, D002, etc.
        doc.subcategory_code = f"{doc.letter_prefix}{next_seq:03d}"
