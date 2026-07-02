# Instalasi Stock Ledger Refactored

Panduan ini menjelaskan cara menginstall atau mengaplikasikan hasil refactoring report **Stock Ledger with SR Fields** ke server ERPNext Anda.

## Prasyarat
- Anda memiliki akses SSH ke server ERPNext.
- Folder ERPNext berada di path standar instalasi Frappe (misalnya: `/home/erpadmin/frappe-bench`).

## Langkah-langkah Instalasi

### 1. Backup Folder Lama (Opsional tapi Direkomendasikan)
Sebelum menimpa file, ada baiknya Anda membackup folder report lama untuk berjaga-jaga.
Buka terminal SSH Anda dan jalankan:
```bash
cd /home/erpadmin/frappe-bench/apps/erpnext/erpnext/stock/report/
cp -r stock_ledger_with_sr_fields stock_ledger_with_sr_fields_backup
```

### 2. Upload File Refactoring
Upload **isi** dari folder `stock_ledger_with_sr_fields_v2` ini ke server Anda, ke dalam direktori:
`/home/erpadmin/frappe-bench/apps/erpnext/erpnext/stock/report/stock_ledger_with_sr_fields/`

> [!IMPORTANT]
> Pastikan nama folder di server **tetap** `stock_ledger_with_sr_fields` (tanpa akhiran `_v2`). File `.py`, `.js`, dan `.json` di dalam server harus tergantikan oleh file dari folder `_v2` ini.

Di dalam folder `stock_ledger_with_sr_fields` di server, seharusnya sekarang berisi:
- `__init__.py`
- `stock_ledger_with_sr_fields.py`
- `stock_ledger_with_sr_fields.js`
- `stock_ledger_with_sr_fields.json`
- `columns.py`
- `procurement.py`
- `queries.py`
- `tree_view.py`

### 3. Restart Bench
Karena Anda memodifikasi file backend Python (`.py`), Anda wajib melakukan restart Gunicorn/Frappe agar perubahan terbaca oleh server.
Di folder bench Anda, jalankan:
```bash
cd /home/erpadmin/frappe-bench/
bench restart
```
Jika Anda menggunakan supervisor, Anda juga bisa merestart lewat supervisor:
```bash
sudo supervisorctl restart all
```

### 4. Selesai!
Buka website ERPNext Anda dan buka laporan **Stock Ledger with SR Fields**. Laporan sekarang sudah menggunakan struktur kode yang baru (modular).
