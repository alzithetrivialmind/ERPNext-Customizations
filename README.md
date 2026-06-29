# ERPNext Customizations

This repository contains Client Scripts, Server Scripts, Query Reports, and Print Formats designed to extend and optimize various workflows in ERPNext.

---

## Directory Overview

The repository is organized by feature and functionality. Each folder contains the necessary scripts, setup instructions, and HTML format templates:

### 1. [Discount Fix](discount_fix)
Implements a highly flexible discount input mechanism supporting:
- **Per-Item Discounts**: Select percentage or absolute amount per line item.
- **Global Discounts**: Apply a total discount value from the header, split equally among all items.
- Works across: `Sales Invoice`, `Sales Order`, `Purchase Invoice`, `Purchase Order`, and `Purchase Receipt`.
- *See the detailed setup and documentation inside the [discount_fix](discount_fix) folder.*

### 2. [Stock Ledger Customizations](Stock%20Ledger)
Customizes the ERPNext Stock Ledger report to provide:
- **Tree View Mode**: Replaces flat tables with chronological time history.
- **Stock Reconciliation Integration**: Retrieves custom fields like PIB details, Historical Supplier, and RDO/RIO dates.
- **Multi-Currency Costing**: Back-calculates transaction values in USD using historical exchange rates.

### 3. Item Management
- **[Item_Creator](Item_Creator)**: A guided DocType and API form that dynamically filters item groups and generates standardized Item Codes using L1-L2-L3 categorization prefix patterns.
- **[Item_List](Item_List)**: Redirects the default "Add Item" button in the Item List view to the `Item Creator` form and provides a premium-styled "Add Service" action.
- **[Item_Sub_Category_Master](Item_Sub_Category_Master)**: Automatically generates sequential subcategory codes (e.g., `D001` → `D002`) based on letter prefixes.

### 4. Purchase & Material Workflows
- **[Material_Request](Material_Request)**: Optimizes layout columns in the items grid, filters subcontracting suppliers, auto-propagates header projects to items, and filters category selections.
- **[Purchase_Order_Print_Status](Purchase_Order_Print_Status)**: Tracks print events on Purchase Orders, adding simple flags and a toolbar button to mark records as printed.
- **[Purchase_Order_Palma](Purchase_Order_Palma)**: Specialized optimizations for PT. Palma Progress Shipyard. Validates and filters item selections based on PO Type, auto-fills default variables, and shows a hover tooltip displaying the last purchase rate for each item.
- **[Purchase_Receipt_PO_Flow](Purchase_Receipt_PO_Flow)**: Enforces that all goods receipts are linked to valid Purchase Orders and locks the rate fields (with an observer mechanism) to protect contracted prices.

### 5. [Print Formats](Print%20Format)
Premium HTML/CSS print format templates for key documents:
- **Material Request**: Custom format templates for Material Requests (Purpose to Issue, Purpose to Purchase).
- **Purchase Order**: Standard print formats for Domestic, Foreign, Service, and Steel material POs.
- **Purchase Receipt**: Custom Goods Receipt layout.
- **Stock Entry**: Optimized format template for stock transfers and adjustments.

---

## Deployment and Setup

Each subdirectory contains its own `README.md` with detailed installation steps. In general, scripts are applied in ERPNext as follows:

### Client Scripts
1. Navigate to **Client Script** → **New**.
2. Select the target **DocType**, set **Apply To** to `Form` (or `List` as specified), and ensure it is enabled.
3. Paste the content of `Client_Script.js` and click **Save**.

### Server Scripts
1. Navigate to **Server Script** → **New**.
2. Select the appropriate **Script Type** (e.g., `Document Event` or `API`).
3. Set the event hook (e.g., `Before Validate`, `Before Save`) or API route name.
4. Paste the content of `Server_Script.py` and click **Save**.
