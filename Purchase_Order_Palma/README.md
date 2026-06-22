# Purchase Order Customizations (Palma Progress Shipyard)

This folder contains complex optimizations for the Purchase Order Form customized for **PT. Palma Progress Shipyard**.

## Features
1. **PO Type-Based Item Filtering**: Dynamically filters items during selection based on the `custom_po_type` field.
   - `Service Order`: Only permits items belonging to the `SV - Services` group and validates that they are non-stock.
   - `PO Steel LN`, `PO Local`, `PO LN`: Excludes any items belonging to the `SV - Services` group.
2. **Auto-Fill Defaults**: Sets the transaction currency, warehouse (`Stores - PPS`), and default terms & conditions on load.
3. **Supplier Attention Auto-population**: Fetches and sets the attention field (`custom_supplier_attention`) from the primary contact of the selected Supplier.
4. **Delayed Description Clearer**: Clears the description field shortly after selecting an item to prevent default descriptions from cluttering rows.
5. **Last Purchase Rate Tooltip**: When hovering over item codes in the grid, fetches and displays a hover tooltip showing the last purchase rate for this item from the current supplier (or displays a message if it is a first-time purchase).

## Setup Instructions

### 1. Custom Fields in ERPNext
Add the following custom fields via **Customize Form**:
- DocType Header (`Purchase Order`):
  - `custom_po_type` (Select, Options: `PO Local`, `PO LN`, `PO Steel LN`, `Service Order`)
  - `custom_supplier_attention` (Data)
- DocType Item (`Purchase Order Item`):
  - (No extra custom fields needed for this, uses standard fields).

### 2. Client Script
- **DocType**: `Purchase Order`
- **Apply To**: `Form`
- **Script**: Paste the contents of `Client_Script.js`

### 3. Server Scripts
Add these 3 API Server Scripts:

#### A. get_last_purchase_rate
- **Script Type**: `API`
- **API Method**: `get_last_purchase_rate`
- **Script**: Paste the contents of `get_last_purchase_rate.py`

#### B. get_filtered_items_for_po
- **Script Type**: `API`
- **API Method**: `get_filtered_items_for_po`
- **Script**: Paste the contents of `get_filtered_items_for_po.py`

#### C. validate_item_for_po_type
- **Script Type**: `API`
- **API Method**: `validate_item_for_po_type`
- **Script**: Paste the contents of `validate_item_for_po_type.py`
