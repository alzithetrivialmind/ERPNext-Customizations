# Setup Custom Fields in ERPNext UI

For the Client Script and Server Script to work correctly, you need to create the following custom fields via the **Customize Form** menu in ERPNext.

---

## PART 1: Custom Fields on the Item Table (Child DocType)

Add these fields to the item child DocType of each transaction you want to enable (e.g., `Sales Invoice Item`, `Sales Order Item`, `Purchase Invoice Item`, etc.).

Go to **Customize Form** → select the target DocType → add the following fields in the `items` grid section:

### 1. Field: custom_user_rate
- **Label:** Base Rate
- **Type:** Currency
- **Options:** currency
- **Insert After:** qty
- **In List View:** Checked (Yes)
- **Columns:** 2

### 2. Field: custom_user_discount_type
- **Label:** Discount Type
- **Type:** Select
- **Options:**
  ```
  
  Percentage
  Amount
  ```
- **Insert After:** custom_user_rate

### 3. Field: custom_user_discount_value
- **Label:** Discount
- **Type:** Float
- **Insert After:** custom_user_discount_type
- **In List View:** Checked (Yes)
- **Columns:** 1

---

**IMPORTANT STEP:**
After adding the 3 fields above, **hide** the following built-in ERPNext fields from the Grid view to avoid confusion. In **Customize Form**, find each field below and **uncheck "In List View"**:
1. `rate`
2. `price_list_rate`
3. `discount_percentage`
4. `discount_amount`

---

## PART 2: Custom Fields on the Header Document (Global Discount)

Add these fields to the header DocType (e.g., `Sales Invoice`, `Purchase Invoice`, `Sales Order`, `Purchase Order`).

Go to **Customize Form** → select the header DocType → add these 2 fields:

### 4. Field: custom_global_discount_type
- **Label:** Global Discount Type
- **Type:** Select
- **Options:**
  ```
  
  Percentage
  Amount
  ```
- **Insert After:** (choose an appropriate field, e.g., after `taxes_and_charges`)

### 5. Field: custom_global_discount_value
- **Label:** Global Discount Value
- **Type:** Float
- **Insert After:** custom_global_discount_type
