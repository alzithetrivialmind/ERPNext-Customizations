# Purchase Order Print Status

This customization tracks whether a Purchase Order has been printed or not by setting a custom print tracking field.

## Features
1. **Toolbar Button**: Adds a "Tandai Sudah Dicetak" (Mark as Printed) button to the toolbar for submitted, unprinted Purchase Orders.
2. **Auto-update on Print**: Automatically sets the printed status when the user prints the Purchase Order.

## Setup Instructions

### 1. Custom Fields
Add a custom field to the **Purchase Order** DocType:
- **Field Name**: `is_printed`
- **Label**: Is Printed
- **Type**: Check

### 2. Client Script
- **DocType**: `Purchase Order`
- **Apply To**: `Form`
- **Script**: Paste the contents of `Client_Script.js`
