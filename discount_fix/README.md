# Setup Custom Fields di UI ERPNext

Agar script UI dan Server berjalan dengan lancar, Anda harus membuat 3 Custom Field ini di setiap transaksi yang Anda butuhkan (contoh: **Sales Invoice Item**, **Sales Order Item**, **Purchase Invoice Item**).

Silakan ke menu **Customize Form**, pilih DocType target (misal: `Sales Invoice Item`), lalu tambahkan baris-baris berikut di bagian grid `items`:

## 1. Field: custom_user_rate
- **Label:** Base Rate
- **Type:** Currency
- **Options:** currency
- **Insert After:** qty
- **In List View:** Centang (Yes)
- **Columns:** 2

## 2. Field: custom_user_discount_type
- **Label:** Discount Type
- **Type:** Select
- **Options:** 
  ```text
  
  Percentage
  Amount
  ```
- **Insert After:** custom_user_rate

## 3. Field: custom_user_discount_value
- **Label:** Discount
- **Type:** Float
- **Insert After:** custom_user_discount_type
- **In List View:** Centang (Yes)
- **Columns:** 1

---
**LANGKAH PENTING:** 
Setelah menambahkan 3 field di atas, **sembunyikan** field bawaan ERPNext ini dari tampilan Grid agar user tidak bingung. Masih di **Customize Form**, cari field-field berikut dan **hilangkan centang "In List View"**:
1. `rate`
2. `price_list_rate`
3. `discount_percentage`
4. `discount_amount`
