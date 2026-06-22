# ERPNext Customizations — Discount Fix

This customization adds a more flexible discount input mechanism to ERPNext transaction documents, supporting both per-item discounts and a global discount applied to all items at once.

---

## Folder Structure

Each folder contains scripts for one specific DocType.
Every folder includes:
- `Client_Script.js` — Paste into the **Client Script** menu in ERPNext
- `Server_Script.py` — Paste into the **Server Script** menu in ERPNext

| Folder | DocType | Description |
|:---|:---|:---|
| `Sales_Invoice/` | Sales Invoice | Customer billing |
| `Sales_Order/` | Sales Order | Customer sales order |
| `Purchase_Invoice/` | Purchase Invoice | Supplier billing |
| `Purchase_Order/` | Purchase Order | Supplier purchase order |
| `Purchase_Receipt/` | Purchase Receipt | Goods receipt — ⚠️ Optional, see note below |

> **Purchase Receipt Note:** Only install these scripts if your business receives goods **without a Purchase Order** first. If your workflow is always PO → PR, the discount is already carried over automatically from the PO — no script needed here.

---

## Custom Fields Required in ERPNext

### A. On the Item Table (Child DocType) — Required for all transactions

Go to **Customize Form** → select the appropriate item DocType → add these 3 fields:

| Header DocType | Item DocType (use this in Customize Form) |
|:---|:---|
| Sales Invoice | Sales Invoice Item |
| Sales Order | Sales Order Item |
| Purchase Invoice | Purchase Invoice Item |
| Purchase Order | Purchase Order Item |
| Purchase Receipt | Purchase Receipt Item |

**Fields to add:**

| Field Name | Label | Type | Options | In List View |
|:---|:---|:---|:---|:---:|
| `custom_user_rate` | Base Rate | Currency | currency | Yes |
| `custom_user_discount_type` | Discount Type | Select | (blank) / Percentage / Amount | No |
| `custom_user_discount_value` | Discount | Float | — | Yes |

**Hide built-in ERPNext fields from Grid View** (uncheck "In List View" for each):
- `rate`
- `price_list_rate`
- `discount_percentage`
- `discount_amount`

---

### B. On the Header Document — Required for the Global Discount feature

Go to **Customize Form** → select the header DocType (e.g., `Sales Invoice`) → add these 2 fields:

| Field Name | Label | Type | Options |
|:---|:---|:---|:---|
| `custom_global_discount_type` | Global Discount Type | Select | (blank) / Percentage / Amount |
| `custom_global_discount_value` | Global Discount Value | Float | — |

Repeat this for every header DocType you activate.

---

## How to Use

### Per-Item Discount
1. Open a transaction document
2. Add items to the item table
3. Fill in the **Discount Type** and **Discount** columns on each row you want to discount
4. Click **Save**

### Global Discount (All Items at Once)
1. Fill in the **Global Discount Type** and **Global Discount Value** fields in the document header
2. Click the **Discount → Apply Global Discount to All Items** button in the toolbar
3. Manually edit individual rows if any item needs a different discount
4. Click **Save**
5. To change and reapply → update the global value → click Apply again (**Reapply**) → Save

---

## Calculation Behavior

| Type | Level | How it works |
|:---|:---|:---|
| Percentage | Per-item | Same % deducted from each unit price |
| Amount (per-item) | Per-row | Total row discount ÷ qty = discount per unit |
| Amount (global) | All rows | Total global ÷ number of rows = discount per row, then ÷ qty for per-unit |

---

## How to Install in ERPNext

### Client Script
- Go to: ERPNext → Client Script → New
- DocType: match the folder name (e.g., `Sales Invoice`)
- Apply To: `Form`
- Paste the contents of `Client_Script.js`

### Server Script
- Go to: ERPNext → Server Script → New
- Script Type: `Document Event`
- Reference DocType: match the folder name (e.g., `Sales Invoice`)
- DocType Event: `Before Validate`
- Paste the contents of `Server_Script.py`
