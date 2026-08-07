# Stock Ledger Customizations

This directory contains Query Report customizations for the **Stock Ledger** module in ERPNext. The primary report extends the standard Stock Ledger with FIFO provenance tracking, multi-currency costing, and Stock Reconciliation field integration.

---

## Directory Structure

| Path | Description |
|:---|:---|
| `stock_ledger_with_sr_fields_v2/` | **Active version** — Refactored, modular codebase (use this for deployment). |
| `stock_ledger_with_sr_fields/` | Previous monolithic version (kept for reference). |
| `Stock Ledger - Original/` | Vanilla ERPNext Stock Ledger report (unmodified backup). |
| `kolom_report_stock_ledger.md` | Detailed documentation of every column in the report. |
| `output/` | Sample output CSV files for verification and comparison. |

---

## Key Features

### 1. FIFO Provenance Tracking
When stock is issued (e.g., via Stock Entry Repack), the report breaks down each outgoing transaction into the original incoming batches using **FIFO queue logic**. Each split row shows:
- **Voucher Type / Voucher #**: The actual transaction consuming the stock (e.g., `Stock Entry`, `MAT-STE-2026-00005`).
- **Origin Voucher Type / Origin Voucher #**: The original document that brought the stock in (e.g., `Stock Reconciliation`, `MAT-RECO-2026-00020`).
- **Origin Posting Date / Origin Posting Time**: When the original incoming transaction occurred.

> This separation ensures that the transactional identity (who consumed the stock) is never overwritten by the provenance identity (who supplied the stock).

### 2. Stock Reconciliation (SR) Custom Fields
If a stock ledger entry originates from a Stock Reconciliation, the report automatically retrieves custom fields:
- Old Item Code (Kode Lama), RDO/RIO Numbers and Dates
- Transaction Type, Historical Supplier
- PIB Data (Number, Year, Month, Date, Exchange Rate)
- Vendor Invoice Data (Invoice Number, Supplier Currency, Rates)

### 3. Multi-Currency & USD Value Calculation
- If the source receipt was in USD, the vendor rate is pulled directly.
- If the currency is not USD, the system fetches historical exchange rates to back-calculate the USD equivalent.
- Exchange rate references and conversion details are displayed per row.

### 4. Procurement Enrichment
For incoming stock from Purchase Receipts or Purchase Invoices, the report traces back to show:
- PO Number & Date
- PR Number & Date
- PI Number & Date
- Vendor Currency, Vendor Rate, IDR Rate, IDR Amount, USD Rate, USD Amount
- Currency Exchange Reference and Exchange Rate (USD to IDR)

### 5. Tree View Mode
The report supports a chronological Tree View layout:
```
[Level 0] ITEM-CODE (Item Name)
  ├── [Level 1] Opening Balance
  │     └── [Level 2] Sisa dari Previous Receipt (FIFO queue remnants)
  ├── [Level 1] Transactions Progress
  │     └── [Level 2] Stock movements during the period (sorted by datetime)
  └── [Level 1] Closing Balance
```

### 6. Total Out Voucher Qty
For outgoing transactions, the report shows the **total quantity** of the parent voucher (e.g., a Stock Entry that issued 2,300 units total), even though the individual FIFO split rows may show smaller quantities.

---

## Module Structure (v2)

The report is split into modular Python files for maintainability:

| File | Purpose |
|:---|:---|
| `stock_ledger_with_sr_fields.py` | Main entry point — orchestrates data fetching, enrichment, and output. |
| `stock_ledger_with_sr_fields.js` | Client-side filter UI (date range, item, warehouse, etc.). |
| `stock_ledger_with_sr_fields.json` | Report metadata (name, type, module). |
| `columns.py` | Column definitions for the report grid. |
| `procurement.py` | FIFO queue logic, provenance enrichment, procurement data fetching. |
| `queries.py` | Database query builders (SLE fetching, currency exchange lookups). |
| `tree_view.py` | Tree View transformation logic (Opening → Transactions → Closing). |
| `__init__.py` | Python package marker. |

---

## Deployment

See [stock_ledger_with_sr_fields_v2/README.md](stock_ledger_with_sr_fields_v2/README.md) for step-by-step installation instructions.

**Quick summary:**
1. Upload the contents of `stock_ledger_with_sr_fields_v2/` to the server at:
   `/home/erpadmin/frappe-bench/apps/erpnext/erpnext/stock/report/stock_ledger_with_sr_fields/`
2. Restart bench: `bench restart`
3. Open the report in ERPNext.

> **Important:** The folder name on the server must remain `stock_ledger_with_sr_fields` (without the `_v2` suffix).

---

## Column Reference

For a complete explanation of every column, including data sources and when/why columns may be empty, see [kolom_report_stock_ledger.md](kolom_report_stock_ledger.md).
