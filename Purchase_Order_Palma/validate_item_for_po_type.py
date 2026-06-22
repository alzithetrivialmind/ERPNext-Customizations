# ==========================================
# SERVER SCRIPT
# Script Type: API
# API Method: validate_item_for_po_type
# Enabled: Yes
# ==========================================

def validate_item_for_po_type(item_code, po_type):
    """
    Validate whether an item is valid for a given PO Type.
    Used for real-time validation when selecting items.
    
    Args:
        item_code: item code to validate
        po_type: PO Type (Service Order, PO Steel LN, PO Local, PO LN)
    
    Returns:
        dict: {
            'valid': True/False,
            'message': error message if invalid
        }
    """
    
    if not item_code or not po_type:
        return {'valid': True, 'message': ''}
    
    # Get item and item_group
    item = frappe.get_doc('Item', item_code)
    item_group_name = item.item_group
    
    # Get item group with lft and rgt values
    item_group = frappe.get_doc('Item Group', item_group_name)
    
    if po_type == "Service Order":
        # Must be SV - Services or descendants
        service_group = frappe.get_doc('Item Group', 'SV - Services')
        
        is_service = (
            item_group_name == 'SV - Services' or
            (item_group.lft >= service_group.lft and item_group.rgt <= service_group.rgt)
        )
        
        if not is_service:
            return {
                'valid': False,
                'message': f'Item "{item_code}" is not in the SV - Services group. Only SV - Services items are allowed for Service Orders.'
            }
        
        if item.is_stock_item == 1:
            return {
                'valid': False,
                'message': f'Item "{item_code}" is a stock item. Service Orders are only allowed for non-stock items.'
            }
            
    elif po_type in ["PO Steel LN", "PO Local", "PO LN"]:
        # Cannot be SV - Services (and descendants)
        service_group = frappe.get_doc('Item Group', 'SV - Services')
        
        is_service = (
            item_group_name == 'SV - Services' or
            (item_group.lft >= service_group.lft and item_group.rgt <= service_group.rgt)
        )
        
        if is_service:
            return {
                'valid': False,
                'message': f'Item "{item_code}" belongs to the SV - Services group. This item is only allowed for Service Orders.'
            }
    
    return {'valid': True, 'message': ''}
