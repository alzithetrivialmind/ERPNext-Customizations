# Final Audit Laporan Rekonsiliasi Stok (Data Integrity Check)

Audit ini dilakukan untuk memverifikasi konsistensi data secara menyeluruh mulai dari data mentah pertama hingga output akhir laporan ERPNext. Ada 4 tahapan file data yang diaudit:

1. **Original Raw Data**: `SM - Sudah dikasih ke Alzi - Sort (1).csv`
2. **Processed Raw Data**: `Raw Data.csv`
3. **ERPNext Import Data**: `Fixed Stock Reconciliation v3.csv`
4. **Final ERPNext Output**: `very new output.csv`

## Metodologi
Pengecekan dilakukan menggunakan script Python yang membaca setiap baris transaksi pada keempat file tersebut dan menjumlahkan metrik utama:
- **Total Qty** (Kuantitas)
- **Total IDR** (Nominal Rupiah) 
- **Total USD** (Nominal Dolar)

> [!NOTE]
> Pada File 3 dan 4, *Total IDR* dihitung ulang menggunakan rumus `Qty * Valuation Rate (Incoming Rate)` untuk memverifikasi kalkulasi di dalam sistem. Termasuk perbaikan pemetaan 3 item ("Data Tidak Ada" yang di-map ulang ke SM-R01-000048, SM-S01-000019B, dan SM-S01-000020).

## Hasil Audit (Grand Totals)

| Tahapan File | Total Quantity | Total Accumulation (IDR) | Total Accumulation (USD) |
|---|---|---|---|
| **1. Original Data** | 29,570.4450 | Rp 151,832,874,856.81 | $9,185,122.80 |
| **2. Processed Raw Data** | 29,570.4450 | Rp 151,832,874,856.81 | $9,185,122.80 |
| **3. Import Data (ERPNext)** | 29,570.4450 | Rp 151,832,874,857.64 | $9,185,122.80 |
| **4. Final Output (ERPNext)** | 29,570.4450 | Rp 151,832,874,857.64 | $9,185,122.80 |

## Analisis & Temuan

> [!TIP]
> **Data Integrity: 100% Valid**
> Semua nilai terkonfirmasi masuk dan terbaca oleh sistem tanpa ada data yang hilang atau terselip.

1. **Kuantitas (Qty)**: Tidak ada perubahan sama sekali dari data awal hingga data akhir. Total kuantitas barang yang diinput adalah tepat **29.570,445**.
2. **Total USD**: Nilai USD konsisten dan akurat pada keempat file sebesar **$9.185.122,80** tanpa ada deviasi pembulatan.
3. **Total IDR & Item Rate**: 
   - Nilai IDR awal adalah **Rp 151.832.874.856,81**.
   - Nilai IDR akhir di laporan adalah **Rp 151.832.874.857,64**.
   - Deviasi (selisih) yang terjadi hanya sebesar **Rp 0,83** (kurang dari 1 Rupiah) untuk total transaksi lebih dari 151 Miliar Rupiah. Selisih ini *murni* karena toleransi pembulatan (*floating point roundoff*). 

## Rincian Item dengan Selisih Pembulatan (Roundoff Differences)

Berikut adalah daftar lengkap 26 item yang mengalami selisih pembulatan desimal. (Item "Data Tidak Ada" sudah tidak ada karena dikalkulasi dan dipetakan sempurna ke kode baru yang valid).

| Item Code | IDR (File 2) | IDR (File 3) | Selisih (Rupiah) |
|---|---|---|---|
| SM-S01-000002 | Rp 52,376,772,146.16 | Rp 52,376,772,147.04 | +0.8800 |
| SM-H01-000004 | Rp 7,201,297,645.31 | Rp 7,201,297,645.22 | -0.0900 |
| SM-A01-000003B | Rp 406,318,887.02 | Rp 406,318,887.10 | +0.0820 |
| SM-S01-000005B | Rp 519,187,697.54 | Rp 519,187,697.49 | -0.0530 |
| SM-S01-000008B | Rp 209,178,612.51 | Rp 209,178,612.47 | -0.0364 |
| SM-S01-000017 | Rp 606,300,968.88 | Rp 606,300,968.91 | +0.0300 |
| SM-S01-000007B | Rp 41,048,891.15 | Rp 41,048,891.16 | +0.0076 |
| SM-S01-000003B | Rp 26,309,596.05 | Rp 26,309,596.06 | +0.0075 |
| SM-A01-000002B | Rp 70,763,172.15 | Rp 70,763,172.16 | +0.0073 |
| SM-A01-000004B | Rp 59,223,471.30 | Rp 59,223,471.31 | +0.0060 |
| SM-A01-000009 | Rp 1,584,872,239.08 | Rp 1,584,872,239.07 | -0.0052 |
| SM-A01-000002 | Rp 1,840,994,679.38 | Rp 1,840,994,679.38 | -0.0050 |
| SM-B01-000027 | Rp 65,999,252.44 | Rp 65,999,252.44 | -0.0043 |
| SM-A01-000012B | Rp 90,929,370.83 | Rp 90,929,370.83 | +0.0040 |
| SM-A01-000011 | Rp 5,235,194,113.22 | Rp 5,235,194,113.22 | +0.0040 |
| SM-S01-000013 | Rp 16,836,213,922.48 | Rp 16,836,213,922.48 | -0.0040 |
| SM-S01-000014B | Rp 749,067,457.61 | Rp 749,067,457.61 | -0.0032 |
| SM-A01-000003 | Rp 3,343,601,781.57 | Rp 3,343,601,781.57 | +0.0030 |
| SM-S01-000013B | Rp 1,051,652,365.30 | Rp 1,051,652,365.30 | -0.0016 |
| SM-A01-000012 | Rp 5,014,953,682.06 | Rp 5,014,953,682.06 | +0.0016 |
| SM-R01-000032 | Rp 55,424,595.26 | Rp 55,424,595.26 | +0.0012 |
| SM-H01-000004B | Rp 83,037,985.66 | Rp 83,037,985.66 | -0.0012 |
| SM-A01-000010B | Rp 29,448,106.19 | Rp 29,448,106.19 | +0.0011 |
| SM-S01-000015B | Rp 9,490,957.34 | Rp 9,490,957.34 | -0.0005 |
| SM-B01-000027B | Rp 10,560,780.61 | Rp 10,560,780.61 | +0.0002 |
| SM-B01-000031B | Rp 3,898,632.03 | Rp 3,898,632.03 | +0.0001 |

**Total Akumulasi Selisih**: +0.8313 Rupiah

## Kesimpulan
Keseluruhan alur rekonsiliasi data stok telah berjalan sangat akurat dan presisi. File custom report mampu menyerap dan menampilkan informasi secara identik dengan data mentah yang telah dirapikan. Selisih yang ada hanyalah toleransi pembulatan pecahan Rupiah (< Rp 1) dari kalkulasi sistem, yang menandakan bahwa proses import `Stock Reconciliation` sukses 100%.
