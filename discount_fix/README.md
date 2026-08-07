# Discount Fix Customizations

Implements a flexible discount entry mechanism for ERPNext transaction documents, supporting both per-item discounts (percentage or absolute amount) and a global discount that can be split across all items.

---

## Architecture

### Scripts per DocType

| Folder | Target DocType | Client Script | Server Script |
|:---|:---|:---:|:---:|
| `Purchase_Order/` | Purchase Order | ✅ | ✅ |
| `Purchase_Receipt/` | Purchase Receipt | ✅ | ✅ *(via PO Flow)* |
| `Purchase_Invoice/` | Purchase Invoice | ✅ | ✅ |
| `Sales_Order/` | Sales Order | ✅ | ✅ |
| `Sales_Invoice/` | Sales Invoice | ✅ | ✅ |

> **Purchase Receipt Note:** The PR has its own Client Script for discount calculation, but the Server Script for PR rate synchronization is handled by the `Purchase_Receipt_PO_Flow` module (separate from this folder). Only install PR-specific discount scripts if your business receives goods **without** a Purchase Order.

### How It Works

**Client Script** (runs in the browser):
- Provides real-time 2-way sync between `custom_palma_base_rate` ↔ `price_list_rate`.
- Recalculates `rate`, `discount_amount`, `discount_percentage` on every change to baseline, discount type, discount amount, or qty.
- Handles the "Apply Global Discount" inline button.

**Server Script** (runs on the server, event: `Before Validate`):
- Authoritative fallback that guarantees correctness even when client-side sync doesn't fire (e.g., API submissions, data imports).
- Uses the same calculation logic as the client script.
- Syncs `base_*` fields (company currency equivalents) using `conversion_rate`.

### Precision Behavior

> **IMPORTANT**: All scripts delegate rounding entirely to ERPNext's native precision system. No `round(..., 2)` or `flt(..., 2)` hardcoding is used.

This means the scripts will automatically respect whatever `Float Precision` and `Currency Precision` values are configured in **System Settings**. This is critical during migration periods where precision may be temporarily set to a higher value (e.g., 9) to preserve data fidelity.

The actual display precision for each currency is ultimately controlled by the **Smallest Currency Fraction Value** in the Currency master data:
- USD with `0.01` → always displays 2 decimals
- IDR with `0.000000000` → follows global System Settings precision

---

## Custom Fields Setup in ERPNext

### A. Item Table Custom Fields (Child DocType)
Add these fields to each child table DocType (`Purchase Order Item`, `Purchase Receipt Item`, `Purchase Invoice Item`, `Sales Order Item`, `Sales Invoice Item`):

| Field Name | Label | Type | Options | Insert After |
|:---|:---|:---|:---|:---|
| `custom_palma_base_rate` | Palma Base Rate | Currency | *(currency)* | `qty` |
| `custom_palma_discount_type` | Palma Discount Type | Select | `Percentage\nAmount` | `custom_palma_base_rate` |
| `custom_palma_discount_amount` | Palma Discount Amount | Currency | — | `custom_palma_discount_type` |

### B. Header Document Custom Fields (Global Discount)
Add these fields to each parent DocType (`Purchase Order`, `Purchase Receipt`, `Purchase Invoice`, `Sales Order`, `Sales Invoice`):

| Field Name | Label | Type | Options | Insert After |
|:---|:---|:---|:---|:---|
| `custom_palma_global_disc_type` | Palma Global Disc Type | Select | `Percentage\nAmount` | `apply_discount_on` |
| `custom_palma_global_disc_value` | Palma Global Disc Value | Currency | — | `custom_palma_global_disc_type` |

> **Note:** ERPNext blocks Data Import for `Custom Field` by default. These fields must be created **manually** via **Customize Form** or the **Custom Field** list.

The `Custom Fields/` subfolder contains CSV templates and utility scripts to assist with field generation.

---

## Script Installation

### Client Script
1. Navigate to **Client Script** → **New**.
2. Set **DocType** (e.g., `Purchase Order`), **Apply To**: `Form`, **Enabled**: ✅.
3. Paste the contents of the relevant `Client_Script.js`.
4. Click **Save**.

### Server Script
1. Navigate to **Server Script** → **New**.
2. Set **Script Type**: `DocType Event`, **Reference DocType** (e.g., `Purchase Order`), **DocType Event**: `Before Validate`.
3. Paste the contents of the relevant `Server_Script.py`.
4. Click **Save**.

---

## Calculation Rules

| Type | Scope | Behavior |
|:---|:---|:---|
| **Percentage** | Per-item | Same percentage deducted from each item's unit price. |
| **Amount** | Per-row | Total row discount, divided by `qty` to get per-unit discount. |
| **Amount** | Global | Global discount ÷ total item rows = per-row discount, then ÷ `qty` for per-unit. |

---

## Utility Scripts

| File | Purpose |
|:---|:---|
| `update_scripts.py` | Batch find-and-replace for renaming custom field references across all scripts. |
| `patch_button.py` | Generates the inline "Apply" button HTML for global discount fields. |
| `Custom Fields/patch_csvs.py` | Patches existing Custom Field CSV exports to add new fields and hide deprecated ones. |
| `Custom Fields/clean_generate.py` | Generates clean Custom Field CSVs from scratch for new installations. |
| `Custom Fields/strip_old.py` | Removes deprecated old field entries from CSV files. |
