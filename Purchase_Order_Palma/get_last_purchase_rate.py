# ==========================================
# SERVER SCRIPT
# Script Type: API
# API Method: get_last_purchase_rate
# Enabled: Yes
# ==========================================

def get_last_purchase_rate(supplier=None, item_code=None):
    """
    Get last purchase rate for an item from a specific supplier.
    
    Args:
        supplier: supplier name (optional - if empty, retrieves from all suppliers)
        item_code: item code to look up
    
    Returns:
        list: [{
            'rate': 280000,
            'name': 'PO-2025-00001',
            'transaction_date': '2025-08-20',
            'supplier': 'CV BOLTINDO SUKSES'
        }, ...]
        
        Sorted by transaction_date DESC (newest first)
    """
    
    if not item_code:
        return []
    
    # Build filters
    filters = {
        'docstatus': 1,  # Submitted only
    }
    
    if supplier:
        filters['supplier'] = supplier
    
    # Query Purchase Order Items containing item_code
    # Join with parent Purchase Order to get supplier and transaction_date
    query = """
        SELECT 
            poi.rate,
            po.name,
            po.transaction_date,
            po.supplier,
            po.supplier_name
        FROM `tabPurchase Order Item` poi
        INNER JOIN `tabPurchase Order` po ON poi.parent = po.name
        WHERE poi.item_code = %(item_code)s
            AND po.docstatus = 1
            {supplier_condition}
        ORDER BY po.transaction_date DESC, po.creation DESC
        LIMIT 10
    """.format(
        supplier_condition="AND po.supplier = %(supplier)s" if supplier else ""
    )
    
    params = {'item_code': item_code}
    if supplier:
        params['supplier'] = supplier
    
    results = frappe.db.sql(query, params, as_dict=True)
    
    # Format results
    formatted = []
    for r in results:
        formatted.append({
            'rate': r.rate or 0,
            'name': r.name,
            'transaction_date': str(r.transaction_date) if r.transaction_date else '',
            'supplier': r.supplier_name or r.supplier or ''
        })
    
    return formatted
