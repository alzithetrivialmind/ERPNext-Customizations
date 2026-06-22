# Item Creator

This customization provides a guided UI and backend logic to generate standardized Item Codes based on Item Group hierarchies (Level 1 → Level 2 → Level 3) and a variant code.

## Features
1. **Dynamic Filtering**: The client script dynamically filters Item Groups so that `group_level_2` only shows children of `group_level_1`, and `group_level_3` only shows children of `group_level_2`.
2. **Standardized Code Generation**: Parses a max 4-character code prefix from Item Group names (e.g. `"SM - Steel Material"` → `"SM"`) and generates a structured base code pattern: `L1-L2-L3` (e.g. `SM-AB-000`).
3. **Variant Selection**: Displays the last created item code for the selected group structure to help users pick the next variant index.
4. **Item Validation & Creation**: Validates and routes/inserts the item into the ERPNext item catalog with the generated code.

## Setup Instructions

### 1. DocType Setup
Create a new DocType called `Item Creator` with the following custom fields:
- `group_level_1` (Link to `Item Group`)
- `group_level_2` (Link to `Item Group`)
- `group_level_3` (Link to `Item Group`)
- `variant_code` (Data)
- `item_name` (Data)
- `stock_uom` (Link to `UOM`)
- `description` (Small Text)
- `preview_code` (Data, read-only)
- `last_code` (Data, read-only)

### 2. Client Script
- **DocType**: `Item Creator`
- **Apply To**: `Form`
- **Script**: Paste the contents of `Client_Script.js`

### 3. Server Script
- **Script Type**: `API`
- **API Method**: `create_item_from_groups_v2`
- **Script**: Paste the contents of `Server_Script.py`
