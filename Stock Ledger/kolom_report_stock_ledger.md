# Penjelasan Kolom: Stock Ledger with SR Fields

Berikut adalah daftar lengkap kolom yang ada pada report ini, beserta penjelasan darimana asal datanya, fungsinya, dan alasan mengapa suatu kolom bisa kosong.

## 1. Kolom Bawaan Stock Ledger (Frappe Standard)

| Kolom | Fungsi & Penjelasan | Kenapa bisa kosong? |
|---|---|---|
| **Date** | Untuk *Normal View*: Menampilkan Tanggal dan Jam transaksi.<br>Untuk *Tree View*: Digunakan sebagai label hierarki (misal: "Opening Balance", "[Item] Nama", dll) | Di Tree view pada baris header/parent akan berisi label, bukan tanggal asli. |
| **Posting Date** | Tanggal transaksi dibukukan. | Kosong pada baris header/Opening/Closing di Tree View. |
| **Posting Time** | Waktu transaksi dibukukan. | Sama seperti di atas. |
| **Item** | Kode item yang bertransaksi. | Kosong pada sub-baris di Tree View untuk menghindari duplikasi visual. |
| **Item Name** | Nama lengkap item. | - |
| **Stock UOM** | Satuan stok (misal: Length, Sheet, dll). | Kosong pada sub-baris di Tree View. |
| **In Qty** | Jumlah barang masuk pada transaksi tersebut. | Kosong jika transaksi adalah barang keluar (Out Qty). |
| **Out Qty** | Jumlah barang keluar pada transaksi tersebut. | Kosong jika transaksi adalah barang masuk (In Qty). |
| **Balance Qty** | Saldo kuantitas barang **setelah** transaksi ini terjadi. | - |
| **Warehouse** | Gudang tempat transaksi terjadi. | Kosong pada baris header Tree View jika filter gudang tidak spesifik. |
| **Incoming Rate** | Harga per satuan untuk barang masuk pada transaksi tersebut (berasal dari PO/Receipt). | Kosong pada transaksi barang keluar (karena barang keluar tidak punya incoming rate, melainkan menggunakan valuation rate). |
| **Valuation Rate** | Harga rata-rata per satuan stok (Moving Average atau FIFO) pada saat transaksi tersebut selesai. | Seharusnya selalu ada, kecuali jika nilai stok habis (0) atau memang belum pernah ada penerimaan dengan harga > 0. |
| **Balance Value** | Total nilai stok (`Balance Qty` × `Valuation Rate`). | - |
| **Value Change** | Perubahan total nilai stok (selisih `Balance Value` saat ini dengan transaksi sebelumnya). | 0 jika transaksi tidak merubah nilai total (misal, pindah gudang tanpa ubah nilai). |
| **Voucher Type** | Jenis dokumen transaksi (Purchase Receipt, Delivery Note, Stock Reconciliation, dll). | - |
| **Voucher #** | Nomor dokumen transaksi. | - |

---

## 2. Kolom Pengayaan dari Dokumen Pembelian (Procurement)

Sistem akan melacak mundur (melalui FIFO atau referensi langsung) dari transaksi untuk mencari dokumen **Purchase Receipt (PR)** atau **Purchase Invoice (PI)** yang mendasari masuknya barang tersebut, lalu menarik data-data berikut:

| Kolom | Fungsi & Penjelasan | Kenapa bisa kosong? |
|---|---|---|
| **Vendor Currency** | Mata uang vendor pada dokumen pembelian. | Kosong jika barang masuk melalui Stock Reconciliation, Stock Entry (Manufacture/Repack), atau jika sistem tidak berhasil melacak dokumen pembelian aslinya. |
| **Vendor Rate** | Harga beli dalam mata uang vendor. | Sama seperti di atas. |
| **IDR Rate** | Harga beli yang dikonversi ke IDR. | Sama seperti di atas. |
| **IDR Amount** | Total harga beli dalam IDR (`IDR Rate` × `Qty`). | Sama seperti di atas. |
| **USD Rate** | Harga beli yang dikonversi ke USD. | Sama seperti di atas. |
| **USD Amount** | Total harga beli dalam USD. | Sama seperti di atas. |
| **Exchange Rate (USD to IDR)**| Nilai tukar USD ke IDR pada saat pembelian. | Kosong jika tidak ada data konversi atau dokumen asalnya adalah IDR murni. |
| **PI No & PI Date** | Nomor dan Tanggal Purchase Invoice. | Kosong jika PR belum ditagihkan (belum dibuat PI), atau barang masuk bukan dari alur pembelian. |
| **PO No & PO Date** | Nomor dan Tanggal Purchase Order. | Kosong jika masuk tanpa PO. |
| **PR No & PR Date** | Nomor dan Tanggal Purchase Receipt. | Kosong jika masuk langsung via PI tanpa PR. |

---

## 3. Kolom Khusus Stock Reconciliation (SR Custom Fields)

Jika suatu barang masuk melalui dokumen **Stock Reconciliation (SR)**, report akan mencoba membaca field-field khusus (Custom Fields) yang ada pada baris Stock Reconciliation Item tersebut.

> **PENTING:** Data-data di bawah ini **HANYA ADA** jika transaksi tersebut adalah `Voucher Type = Stock Reconciliation`. Jika transaksinya berupa Purchase Receipt, Stock Entry, Delivery Note, dsb, maka seluruh kolom SR ini **PASTI KOSONG**.

| Kolom | Asal Field (Frappe) | Penjelasan |
|---|---|---|
| **SR Kode Lama** | `custom_sr_kode_lama` | Kode item sistem lama. |
| **SR No RDO** | `custom_sr_no_rdo` | Nomor RDO (Request Delivery Order). |
| **SR Tanggal RDO** | `custom_sr_tanggal_rdo` | Tanggal dokumen RDO. |
| **SR No RIO** | `custom_sr_no_rio` | Nomor RIO (Request Issue Order). |
| **SR Tanggal RIO** | `custom_sr_tanggal_rio` | Tanggal dokumen RIO. |
| **SR Transaction Type** | `custom_sr_transaction_type`| Tipe transaksi saat stok direkonsiliasi. |
| **SR Supplier Historis** | `custom_sr_supplier_historis`| Nama supplier historis (dijaga jika direkonsiliasi manual). |
| **SR No PIB** | `custom_sr_no_pib` | Nomor Pemberitahuan Impor Barang. |
| **SR Tahun PIB** | `custom_sr_tahun_pib` | Tahun dokumen PIB. |
| **SR Bulan PIB** | `custom_sr_bulan_pib` | Bulan dokumen PIB. |
| **SR Tanggal PIB** | `custom_sr_tanggal_pib` | Tanggal dokumen PIB. |
| **SR Kurs pada PIB** | `custom_sr_kurs_pada_pib` | Kurs mata uang saat impor (PIB). |
| **SR No Invoice Vendor**| `custom_sr_no_invoice_vendor`| Nomor invoice asli dari vendor. |
| **SR Tahun doc RDO** | `custom_sr_tahun_doc_rdo` | Tahun RDO diterbitkan. |
| **SR Qty Invoice** | `custom_sr_qty_invoice` | Qty yang tertera di Invoice vendor. |
| **SR Supplier Currency**| `custom_sr_supplier_currency`| Mata uang supplier. |
| **SR Harga Supplier** | `custom_sr_harga_supplier` | Harga asli supplier. |
| **SR Total dari Supplier**| `custom_sr_total_dari_supplier`| Total harga (Qty × Harga). |
| **SR Kurs ke IDR** | `custom_sr_kurs_ke_idr` | Nilai tukar supplier currency ke IDR saat rekonsiliasi. |
| **SR Kurs ke USD** | `custom_sr_kurs_ke_usd` | Nilai tukar IDR ke USD saat rekonsiliasi. |
| **SR Total in USD** | `custom_sr_total_in_usd` | Total nilai rekonsiliasi ekuivalen USD. |

### Mengapa SR Kosong di Output 06?
Pada *Output 06 (Bulanan - Juni)*, jika tidak ada transaksi Stock Reconciliation pada bulan Juni, maka wajar tidak ada satupun kolom SR yang terisi. Meskipun baris "Opening Balance (Sisa dari ...)" muncul, baris tersebut bukan dokumen transaksi, melainkan saldo virtual bawaan FIFO, sehingga detil dokumen custom-nya tidak ditarik secara spesifik jika bukan berasal langsung dari dokumen transaksi SR di bulan tersebut. (Meski di script kita telah mencoba mem-passing `procurement details` dari pieces, yang berisi data SR juga).
