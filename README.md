# ERPNext Customizations

> **PT. Palma Progress Shipyard** — ERPNext v15 Custom Scripts, Query Reports, Print Formats, and Utilities.

This repository contains Client Scripts, Server Scripts, Query Reports, and Print Formats designed to extend and optimize various workflows in ERPNext.

---

## Directory Overview

The repository is organized by feature and functionality. Each folder contains the necessary scripts, setup instructions, and HTML format templates.

### 1. [Discount Fix](discount_fix)
Implements a flexible discount input mechanism for transaction documents, supporting:
- **Per-Item Discounts**: Percentage-based or absolute amount per line item.
- **Global Discounts**: Apply a total discount value from the header, split equally among all items.
- Works across 5 DocTypes: `Purchase Order`, `Purchase Receipt`, `Purchase Invoice`, `Sales Order`, `Sales Invoice`.
- Uses custom fields prefixed with `custom_palma_*` to avoid collisions with ERPNext built-in fields.
- **Precision Behavior**: All scripts delegate rounding to ERPNext's native `Float Precision` / `Currency Precision` settings in System Settings. No hardcoded decimal precision is used — this ensures safe operation during migration periods where precision may be temporarily set higher (e.g., 9).

> See detailed setup and documentation in the [discount_fix](discount_fix) folder.

### 2. [Stock Ledger Customizations](Stock%20Ledger)
Custom Query Report that extends the standard ERPNext Stock Ledger:
- **FIFO Provenance Tracking**: Breaks down outgoing stock movements into their original incoming batches using FIFO logic, showing exactly which Purchase Receipt or Stock Reconciliation provided each unit of stock.
- **Stock Reconciliation Integration**: Retrieves custom fields like PIB details, Historical Supplier, RDO/RIO dates from `Stock Reconciliation Item` records.
- **Multi-Currency Costing**: Back-calculates transaction values in USD using historical exchange rates.
- **Tree View Mode**: Chronological time-history layout (Opening Balance → Transactions → Closing Balance) for FIFO cost traceability.

> See detailed column documentation in [kolom_report_stock_ledger.md](Stock%20Ledger/kolom_report_stock_ledger.md).

### 3. Item Management
- **[Item_Creator](Item_Creator)**: A guided DocType and API form that dynamically filters item groups and generates standardized Item Codes using L1-L2-L3 categorization prefix patterns.
- **[Item_List](Item_List)**: Redirects the default "Add Item" button in the Item List view to the `Item Creator` form and provides a premium-styled "Add Service" action.
- **[Item_Sub_Category_Master](Item_Sub_Category_Master)**: Automatically generates sequential subcategory codes (e.g., `D001` → `D002`) based on letter prefixes.

### 4. Purchase & Material Workflows
- **[Material_Request](Material_Request)**: Optimizes layout columns in the items grid, filters subcontracting suppliers, auto-propagates header projects to items, and filters category selections.
- **[Purchase_Order_Print_Status](Purchase_Order_Print_Status)**: Tracks print events on Purchase Orders, adding simple flags and a toolbar button to mark records as printed.
- **[Purchase_Order_Palma](Purchase_Order_Palma)**: Specialized optimizations for PT. Palma Progress Shipyard. Validates and filters item selections based on PO Type, auto-fills default variables (currency, warehouse, terms), fetches supplier attention from primary contact, and shows a hover tooltip displaying the last purchase rate for each item.
- **[Purchase_Receipt_PO_Flow](Purchase_Receipt_PO_Flow)**: Enforces that all goods receipts are linked to valid Purchase Orders and locks the rate fields (with an observer mechanism) to protect contracted prices. Includes a `Before Validate` server hook that forces PR currency to match the linked PO currency, fixing a core ERPNext bug where supplier defaults silently override the mapped currency.

### 5. [Print Formats](Print%20Format)
Premium HTML/CSS print format templates for key documents:
- **Material Request**: Custom format templates for Material Requests (Purpose to Issue, Purpose to Purchase).
- **Purchase Order**: Standard print formats for Domestic, Foreign, Service, and Steel material POs.
- **Purchase Receipt**: Custom Goods Receipt layout.
- **Stock Entry**: Optimized format template for stock transfers and adjustments.

### 6. [Stock Reconciliation](Stock%20Reconciliation) (Data Files)
Contains data files, audit reports, and outputs related to the initial stock migration / reconciliation process. All CSV files are gitignored as they contain company-specific data.

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

### Query Reports (Stock Ledger)
1. Upload the `.py`, `.js`, `.json` files to the server filesystem under the Frappe app's report directory.
2. Restart bench (`bench restart`) to load the new Python modules.
3. See the [Stock Ledger v2 README](Stock%20Ledger/stock_ledger_with_sr_fields_v2/README.md) for detailed steps.

---

## Known Behaviors & Notes

### Floating-Point Precision on IDR Amounts
When `Float Precision` or `Currency Precision` in System Settings is set to a high value (e.g., 9), IDR amounts may display trailing decimal noise (e.g., `990,000,000.000000715`). This is caused by ERPNext core's internal `calculate_taxes_and_totals()` pipeline — **not** by any custom script in this repository. The noise disappears when precision is set back to 2.

Additionally, the display precision for each currency is controlled by the **Smallest Currency Fraction Value** field in the Currency master data (e.g., `Currency > USD`). If this value is set to `0.01` for USD but `0.000000000` for IDR, USD will always display 2 decimals regardless of global precision settings, while IDR will follow the global setting.

### Multi-Currency Validation on Purchase Receipt
ERPNext core has a known behavior where creating a Purchase Receipt from a foreign-currency PO can fail with `Currency must be equal to 'SGD'` (or similar). This is caused by the supplier's default billing currency silently overriding the mapped PO currency on the server side. The `Purchase_Receipt_PO_Flow` Server Script includes a `Before Validate` hook to fix this. See [incident_report.md](incident_report.md) for full root cause analysis.
