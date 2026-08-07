# Incident Report: Multi-Currency Validation Error on Purchase Receipt

**Date:** 07 August 2026  
**Incident:** `frappe.exceptions.ValidationError: Incorrect value:Currency must be equal to 'SGD'` during Purchase Receipt saving.

## Executive Summary
When attempting to create a Purchase Receipt (PR) from a foreign-currency Purchase Order (PO), the system persistently rejected the save action with a validation error complaining about a currency mismatch. Extensive isolation testing proved this was not caused by the `discount_fix` client or server scripts, but was rooted in core ERPNext behavior related to Supplier defaults. The issue was successfully mitigated by injecting a server-side hook to force currency synchronization.

## Root Cause Analysis
1. **The Scenario:** A Purchase Order was created using a foreign currency (e.g., SGD). 
2. **The ERPNext Core Behavior:** When the user clicks "Create > Purchase Receipt", ERPNext successfully maps the PO currency (SGD) to the new PR on the client side. The user's screen correctly displays SGD.
3. **The Silent Override:** When the user clicks "Save", the data is sent to the server. During the `set_missing_values` or similar initialization phase on the server, ERPNext checks the default `Billing Currency` of the Supplier. Because the Supplier (e.g., `ADJUSTMENT COMPANY`) was historically locked to `IDR` (or had no default, defaulting to Company Currency `IDR`), the system **silently overwrote** the PR's currency back to `IDR` before running standard validations.
4. **The Validation Failure:** The `TransactionBase` validation logic (`validate_with_previous_doc`) then ran. It compared the PR's currency (now `IDR`) against the PO's currency (`SGD`). Recognizing the mismatch, it threw the error: `Currency must be equal to 'SGD'`.

## Resolution
To override this unwanted core behavior, a server-side script hook was implemented on `Purchase Receipt`:
- **Event:** `Before Validate`
- **Action:** The script traverses the PR items, identifies the linked Purchase Order, fetches the original PO document, and forces the PR's `currency`, `buying_price_list`, and `conversion_rate` to exactly match the PO.
- **Result:** Because this hook runs *after* the silent override but *before* the final validation, the validation now receives the correct foreign currency (e.g., SGD) and passes flawlessly.

## Next Steps
The custom fields from the `discount_fix` module are being refactored to use unique names (`custom_palma_*`) to prevent any potential future conflicts, and all associated print formats and scripts are being updated accordingly.
