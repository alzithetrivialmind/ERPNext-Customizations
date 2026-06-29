# Stock Ledger Customizations

This directory contains Query Report customizations for the **Stock Ledger** module in ERPNext. The primary customizations focus on adding transaction-specific columns (Custom Fields) and restructuring the layout into a chronological Tree View.

## Reports List
- **Stock Ledger with SR Fields** (`stock_ledger_with_sr_fields`)
  This report is a derivative and modification of the standard ERPNext *Stock Ledger* report.

## Key Features of "Stock Ledger with SR Fields"

### 1. Addition of Stock Reconciliation (SR) Fields
The report has been enriched to fetch data directly from *Stock Reconciliation Item* records. If a *Stock Ledger Entry* (SLE) originates from a *Stock Reconciliation*, the report automatically retrieves custom fields such as:
- Old Item Code (Kode Lama)
- RDO Number & Date
- RIO Number & Date
- Transaction Type
- Historical Supplier
- PIB Data (PIB Number, Year, Month, Date, and Exchange Rate at PIB)
- Vendor Invoice Data (Invoice Number, USD Exchange Rate, etc.)

### 2. Multi-Currency & USD Value Calculation
The report automatically calculates and displays the transaction value in USD:
- If the source receipt (Purchase Receipt / Purchase Invoice) was recorded in USD, the report pulls the *vendor rate* directly.
- If the currency is not USD, the system fetches historical exchange rates (from USD to IDR) for the transaction month to back-calculate the equivalent value in USD.

### 3. Chronological, History-Based FIFO Tree View
This is a significant overhaul of the standard flat table format:
- The report can be toggled into a **Tree View**.
- The tree structure is ordered **chronologically (time history)** rather than being split into "Inward" and "Outward".
- **Hierarchical Report Structure:**
  - `[Level 0] ITEM-CODE (Item Name)`
    - `[Level 1] Opening Balance`
      - `[Level 2] (Opening Details)`: The remaining queue of incoming stock (FIFO tail) from previous months that forms the starting balance of the current period.
    - `[Level 1] Transactions Progress`
      - `[Level 2]`: Stock movement history (consolidated PR, PI, Issue, etc.) during the current month, sorted precisely by date and time.
    - `[Level 1] Closing Balance`

The advantage of this format is that users (especially the Accounting team) can trace FIFO costing transparently, understand exactly where the opening balance figures came from, and read stock movements chronologically like a bank passbook.

## Deployment Instructions
Since this is a *Query Report*, you can create or replace it on your ERPNext instance as follows:
1. Navigate to the **Report** DocType in ERPNext.
2. Create a new report (or modify the existing `Stock Ledger with SR Fields` report).
3. Set **Report Type** to `Query Report`.
4. Copy the `.py` and `.js` code into the corresponding directory on your Frappe server filesystem, or adjust the path so that it is properly loaded by your Frappe app.
