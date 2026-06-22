# Item List Customization

This customization overrides the default behavior of the **Item List** view.

## Features
1. **Redirect "Add Item"**: Clicking the primary "Add Item" button redirects users to create a new `Item Creator` document instead of the default Item form.
2. **Add Service**: Adds a secondary button "Add Service" that redirects users directly to a new Item form with preset values for non-stock services (`item_group: 'SE - Services'`, `is_stock_item: 0`).
3. Styled buttons to a premium black/white theme.

## Installation

### Client Script
- **DocType**: `Item`
- **Apply To**: `List`
- **Script**: Paste the contents of `Client_Script.js`
