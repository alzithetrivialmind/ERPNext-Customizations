# ==========================================
# SERVER SCRIPT
# Script Type: API / Custom Query
# API Method: get_filtered_items_for_po
# Enabled: Yes
# ==========================================

def get_filtered_items_for_po(doctype, txt, searchfield, start, page_len, filters):
    """Filter items based on PO Type with nested set query"""
    
    po_type = filters.get('po_type')
    
    if not po_type:
        return frappe.get_all(
            'Item',
            filters={'disabled': 0},
            fields=['name'],
            as_list=True,
            limit_start=start,
            limit_page_length=page_len
        )
    
    search_condition = ""
    if txt:
        search_condition = """AND (
            item.name LIKE %(txt)s 
            OR item.item_name LIKE %(txt)s 
            OR item.item_code LIKE %(txt)s
        )"""
    
    if po_type == "Service Order":
        query = """
            SELECT DISTINCT item.name
            FROM `tabItem` item
            INNER JOIN `tabItem Group` ig_item ON item.item_group = ig_item.name
            INNER JOIN `tabItem Group` ig_service ON ig_service.name = 'SV - Services'
            WHERE item.disabled = 0
                AND item.is_stock_item = 0
                AND (
                    item.item_group = 'SV - Services'
                    OR (ig_item.lft >= ig_service.lft AND ig_item.rgt <= ig_service.rgt)
                )
                {search_condition}
            ORDER BY item.name
            LIMIT {start}, {page_len}
        """.format(
            search_condition=search_condition,
            start=start,
            page_len=page_len
        )
        
    elif po_type in ["PO Steel LN", "PO Local", "PO LN"]:
        # PO Steel LN / PO Local / PO LN: exclude only SV - Services
        query = """
            SELECT DISTINCT item.name
            FROM `tabItem` item
            INNER JOIN `tabItem Group` ig_item ON item.item_group = ig_item.name
            LEFT JOIN `tabItem Group` ig_service ON ig_service.name = 'SV - Services'
            WHERE item.disabled = 0
                AND item.item_group != 'SV - Services'
                AND NOT (ig_item.lft >= ig_service.lft AND ig_item.rgt <= ig_service.rgt)
                {search_condition}
            ORDER BY item.name
            LIMIT {start}, {page_len}
        """.format(
            search_condition=search_condition,
            start=start,
            page_len=page_len
        )
        
    else:
        query = """
            SELECT DISTINCT item.name
            FROM `tabItem` item
            WHERE item.disabled = 0
                {search_condition}
            ORDER BY item.name
            LIMIT {start}, {page_len}
        """.format(
            search_condition=search_condition,
            start=start,
            page_len=page_len
        )
    
    return frappe.db.sql(query, {'txt': '%' + txt + '%'} if txt else {}, as_list=True)
