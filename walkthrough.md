# Panduan Pemulihan: Discount Fix Module

Berikut adalah langkah-langkah yang perlu dilakukan di ERPNext untuk mengaktifkan sistem discount fix dengan penamaan field `custom_palma_*`.

---

## 1. Pembuatan Custom Fields

Karena kebijakan keamanan ERPNext memblokir Data Import untuk `Custom Field`, pembuatan field harus dilakukan **secara manual** melalui menu **Customize Form** atau **Custom Field** list.

### A. Untuk Item Table (Child DocType)
Buat 3 field berikut di setiap child DocType: `Purchase Order Item`, `Purchase Receipt Item`, `Purchase Invoice Item`, `Sales Order Item`, `Sales Invoice Item`.

| Label | Name | Type | Options | Insert After |
|---|---|---|---|---|
| Palma Base Rate | `custom_palma_base_rate` | Currency | *(currency)* | `qty` |
| Palma Discount Type | `custom_palma_discount_type` | Select | `Percentage\nAmount` | `custom_palma_base_rate` |
| Palma Discount Amount | `custom_palma_discount_amount` | Currency | — | `custom_palma_discount_type` |

### B. Untuk Header (Parent DocType)
Buat 2 field berikut di setiap parent DocType: `Purchase Order`, `Purchase Receipt`, `Purchase Invoice`, `Sales Order`, `Sales Invoice`.

| Label | Name | Type | Options | Insert After |
|---|---|---|---|---|
| Palma Global Disc Type | `custom_palma_global_disc_type` | Select | `Percentage\nAmount` | `apply_discount_on` |
| Palma Global Disc Value | `custom_palma_global_disc_value` | Currency | — | `custom_palma_global_disc_type` |

---

## 2. Aktifkan Semua Script

Setelah field-field tersebut selesai dibuat:

1. Buka **Client Script List** di ERPNext.
2. Untuk setiap DocType (PO, PR, PI, SO, SI):
   - Buat Client Script baru → **DocType**: sesuai, **Apply To**: `Form`, **Enabled**: ✅
   - Copy-paste isi `Client_Script.js` dari folder yang sesuai di repository.
3. Buka **Server Script List** di ERPNext.
4. Untuk setiap DocType yang memiliki Server Script:
   - Buat Server Script baru → **Script Type**: `DocType Event`, **DocType Event**: `Before Validate`
   - Copy-paste isi `Server_Script.py` dari folder yang sesuai di repository.

> **PENTING:** Jangan lupa juga mengupdate Server Script `PR - Custom PO Flow` (`Purchase_Receipt_PO_Flow/Server_Script.py`) dengan event `Before Validate`. Script ini mencegah error **"Currency must be equal to 'SGD'"** saat membuat Purchase Receipt dari PO foreign currency.

---

## 3. Update Print Format

Karena nama field base rate telah diubah menjadi `custom_palma_base_rate`, Format Print HTML yang lama perlu diupdate.

1. Buka **Print Format List**.
2. Buka keempat format print Purchase Order yang custom (LN, Local, Service Order, Steel LN).
3. Copy-paste kode HTML yang baru dari folder repository `Print Format/Purchase Order/...` ke dalam ERPNext.

---

## 4. Pengujian Akhir

Setelah semuanya terpasang:
- Buat Purchase Order baru dengan mata uang Asing (misal USD atau SGD).
- Masukkan item, atur Palma Base Rate, berikan diskon, lalu Save dan Submit.
- Klik tombol **Create > Purchase Receipt**.
- Simpan Purchase Receipt tersebut.

Proses simpan akan berhasil tanpa validasi error seputar mata uang.
