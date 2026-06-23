# Stock Ledger Customizations

Direktori ini berisi kustomisasi Query Report untuk modul **Stock Ledger** di ERPNext. Kustomisasi utama difokuskan pada penambahan kolom spesifik (*Custom Fields*) dan restrukturisasi tampilan pohon (*Tree View*).

## Daftar Report
- **Stock Ledger with SR Fields** (`stock_ledger_with_sr_fields`)
  Laporan ini merupakan turunan dan modifikasi dari laporan standar *Stock Ledger*.

## Fitur Utama "Stock Ledger with SR Fields"

### 1. Penambahan Kolom Stock Reconciliation (SR) Fields
Laporan ini telah diperkaya dengan penarikan data dari *Stock Reconciliation Item*. Jika sebuah *Stock Ledger Entry* (SLE) berasal dari *Stock Reconciliation*, laporan akan secara otomatis menarik data *custom fields* seperti:
- Kode Lama
- Nomor & Tanggal RDO
- Nomor & Tanggal RIO
- Tipe Transaksi
- Supplier Historis
- Data PIB (Nomor, Tahun, Bulan, Tanggal, Kurs pada PIB)
- Data Invoice Vendor (Nomor Invoice, Kurs USD, dsb.)

### 2. Multi-Currency & Kalkulasi Nilai USD
Laporan secara otomatis menghitung nilai USD. Jika sumber penerimaan (Purchase Receipt/Purchase Invoice) menggunakan mata uang USD, laporan langsung menarik *vendor rate*. Jika selain USD, sistem akan menarik data kurs (Exchange Rate) historis pada bulan terjadinya transaksi dari USD ke IDR untuk mengalkulasi mundur ke ekuivalen USD.

### 3. Tree View Kronologis Berbasis Histori & FIFO
Ini adalah perombakan besar dari format tabel (*flat table*) standar:
- Laporan bisa di-*toggle* menjadi **Tree View**.
- Struktur pohon diurutkan secara **kronologis (histori waktu)**, bukan dipecah berdasarkan "Inward" (Masuk) dan "Outward" (Keluar).
- **Struktur Hierarki Laporan:**
  - `[Level 0] ITEM-CODE (Item Name)`
    - `[Level 1] Opening Balance`
      - `[Level 2] (Opening Details)`: Sisa antrean penerimaan (*Ekor FIFO*) dari bulan-bulan sebelumnya yang membentuk saldo awal periode saat ini.
    - `[Level 1] Transactions Progress`
      - `[Level 2]`: Riwayat pergerakan stok (gabungan PR, PI, Issue, dsb) dalam bulan berjalan, diurutkan secara presisi berdasarkan tanggal dan waktu.
    - `[Level 1] Closing Balance`

Keunggulan dari format ini adalah pengguna (terutama tim *Accounting*) dapat melacak *costing* FIFO secara transparan, memahami darimana angka saldo awal berasal, dan membaca pergerakan stok layaknya sebuah buku tabungan kronologis.

## Cara Pemasangan (Deployment)
Karena laporan ini berbasis *Query Report*, Anda dapat langsung menimpa atau membuat laporan baru di instance ERPNext Anda:
1. Masuk ke DocType **Report**.
2. Buat report baru (atau modifikasi `Stock Ledger with SR Fields`).
3. Set **Report Type** menjadi `Query Report`.
4. Salin kode `.py` dan `.js` ke dalam modul ERPNext di *server file system*, atau sesuaikan agar dibaca oleh sistem Frappe Anda.
