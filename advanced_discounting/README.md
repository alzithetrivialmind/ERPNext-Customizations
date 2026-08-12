# Advanced Discounting

Frappe custom app for ERPNext V15 — provides PO→PR proportional discount allocation and PI/PR discount management for PT. Palma Progress Shipyard.

## Modules

### Module 1 — Discount Allocation (PO → PR)
Proportionally allocates PO-level discounts across multiple Purchase Receipts based on received quantities. Ensures consistent stock valuation rates by writing to ERPNext's standard `discount_amount` field.

### Module 2 — Purchase Discounting (PI/PR)
Migrated from legacy Client Script + Server Script. Provides 2-way sync between `custom_palma_base_rate` and `price_list_rate`, per-row discount calculation, and value-weighted global discount distribution.

## Installation

```bash
# From the bench directory:
bench get-app /path/to/advanced_discounting
bench --site <site> install-app advanced_discounting
bench --site <site> migrate
```

> **IMPORTANT**: Disable ALL legacy Client Scripts and Server Scripts for Purchase Invoice, Purchase Receipt, and Purchase Order (`discount_fix/` folder) **before** installing this app.

## Phase 2 TODOs
- `permlevel` / role restriction on `custom_disc_is_historical`
- Read-only-after-submit lock on `custom_disc_is_historical`
