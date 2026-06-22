# Material Request Customizations

This customization optimizes the Material Request form layout, enforces field requirements dynamically based on document types, and simplifies column visibility in the items table.

## Features
1. **Dynamic Item Grid Layout**: Keeps only the most relevant columns visible in the items grid:
   `Item Code` | `Qty` | `UoM` | `Item Name` | `Item Group` | `Actual Qty` | `Project` | `Description`
2. **Project Filter & Auto-fill**: Filters out completed/cancelled projects in the header and automatically copies the selected project to all item rows.
3. **Subcontractor Filtering**: Restricts subcontractor fields to show only suppliers from "Subcontractor" or "Palma Internal" supplier groups.
4. **Item Code Group Filtering**: Automatically restricts item code autocomplete in the table to matches belonging to the selected header Item Group/Category.
5. **Conditional Required Fields**: Enforces that `project`, `custom_subcontractor`, and `item_group` fields are mandatory if the Material Request type is either "Material Issue" or "Purchase".

## Setup Instructions

### Client Script
- **DocType**: `Material Request`
- **Apply To**: `Form`
- **Script**: Paste the contents of `Client_Script.js`
