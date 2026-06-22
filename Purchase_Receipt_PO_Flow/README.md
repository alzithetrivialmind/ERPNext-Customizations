# Purchase Receipt PO Flow

This customization enforces that every receipt of goods is linked to a pre-existing Purchase Order, and prevents unauthorized changes to item prices at the time of receipt.

## Features
1. **Custom PO Linker Button**: Replaces ERPNext's standard "Get Items From Purchase Order" with a custom button "Pilih Purchase Order".
2. **Dynamic PO Filtering**: Filters POs to show only those belonging to the selected Supplier and whose status is either "To Receive and Bill" or "To Receive".
3. **Price Protection & Locking**: Automatically fetches the correct item price from the PO and locks the `rate` and `price_list_rate` fields to read-only. An observer runs every 500ms to automatically restore PO rates if any script attempt to override them.
4. **Link Enforcer (Before Save)**: A server-side Document Event script validates that every item row in the items grid is linked to a valid `purchase_order` and `purchase_order_item` row. It throws an error if any unlinked items are saved.

## Setup Instructions

### 1. Client Script
- **DocType**: `Purchase Receipt`
- **Apply To**: `Form`
- **Script**: Paste the contents of `Client_Script.js`

### 2. Server Script
- **DocType**: `Purchase Receipt`
- **Script Type**: `Document Event`
- **DocType Event**: `Before Save` (or `Before Validate`)
- **Script**: Paste the contents of `Server_Script.py`
