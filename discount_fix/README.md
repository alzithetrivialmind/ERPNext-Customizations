# Discount Fix Customizations

This folder contains Client and Server Scripts designed to implement a flexible discount entry mechanism in ERPNext transaction documents. It supports both per-item discounts (either percentage-based or absolute amount) and a global discount that can be split or applied across all items simultaneously.

---

## Folder Structure

Each subfolder corresponds to a specific ERPNext DocType and contains:
- `Client_Script.js` — Paste into the ERPNext **Client Script** editor.
- `Server_Script.py` — Paste into the ERPNext **Server Script** editor.

| Folder | Target DocType | Description |
|:---|:---|:---|
| `Sales_Invoice/` | Sales Invoice | Customer billing |
| `Sales_Order/` | Sales Order | Customer sales order |
| `Purchase_Invoice/` | Purchase Invoice | Supplier billing |
| `Purchase_Order/` | Purchase Order | Supplier purchase order |
| `Purchase_Receipt/` | Purchase Receipt | Goods receipt — ⚠️ Optional (see note below) |

> **Purchase Receipt Note:** Only install scripts for the Purchase Receipt DocType if your business receives goods **without a Purchase Order** first. If your workflow is always PO → PR, the discount information is already carried over automatically from the PO, so scripts are not needed here.

---

## Custom Fields Setup in ERPNext

To make these scripts work correctly, you must create the following custom fields using the **Customize Form** tool in ERPNext.

### A. Item Table Custom Fields (Child DocType)
Add these fields to the child table DocType of each transaction (e.g., `Sales Invoice Item` for `Sales Invoice`, `Purchase Order Item` for `Purchase Order`, etc.):

| Field Name | Label | Type | Options | In List View | Columns | Insert After |
|:---|:---|:---|:---|:---:|:---:|:---|
| `custom_custom_base_rate` | Base Rate | Currency | currency | Yes | 2 | `qty` |
| `custom_custom_discount_type` | Discount Type | Select | `\nPercentage\nAmount` | No | — | `custom_custom_base_rate` |
| `custom_new_custom_discount` | Discount | Float | — | Yes | 1 | `custom_custom_discount_type` |

**IMPORTANT:**
To avoid UI confusion, **uncheck "In List View"** for the following standard ERPNext fields in the child table Customize Form grid:
1. `rate`
2. `price_list_rate`
3. `discount_percentage`
4. `discount_amount`

---

### B. Header Document Custom Fields (Global Discount)
Add these fields to the main header DocType (e.g., `Sales Invoice`, `Purchase Order`, etc.):

| Field Name | Label | Type | Options | Insert After |
|:---|:---|:---|:---|:---|
| `custom_new_global_discount_type` | Global Discount Type | Select | `\nPercentage\nAmount` | (e.g., after `taxes_and_charges`) |
| `custom_new_global_discount_value` | Global Discount Value | Float | — | `custom_new_global_discount_type` |

---

## Script Setup & Installation

For each transaction DocType you want to customize:

### 1. Setup Client Script
1. Navigate to **Client Script** → click **New**.
2. Set the following:
   - **DocType**: Match the transaction type (e.g., `Sales Invoice`)
   - **Apply To**: `Form`
   - **Enabled**: Checked
3. Copy the contents of the transaction's `Client_Script.js` (e.g., `discount_fix/Sales_Invoice/Client_Script.js`) and paste it into the script editor.
4. Click **Save**.

### 2. Setup Server Script
1. Navigate to **Server Script** → click **New**.
2. Set the following:
   - **Script Type**: `DocType Event`
   - **Reference Document Type**: Match the transaction type (e.g., `Sales Invoice`)
   - **DocType Event**: `Before Validate`
   - **Disabled**: Unchecked (keep enabled)
3. Copy the contents of the transaction's `Server_Script.py` (e.g., `discount_fix/Sales_Invoice/Server_Script.py`) and paste it into the script editor.
4. Click **Save**.

---

## Calculation Rules

| Type | Discount Level | Behavior |
|:---|:---|:---|
| **Percentage** | Per-item | Same percentage deducted from each item's unit price. |
| **Amount (per-item)** | Per-row | The discount value is treated as the total discount for the entire row, and is divided by `qty` to calculate the unit rate discount. |
| **Amount (global)** | All rows | The global discount amount is split equally among all item rows (Global Discount ÷ Total Item Rows). The resulting row discount is then divided by each item's `qty` to find the unit rate discount. |
