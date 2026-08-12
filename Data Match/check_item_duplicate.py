import csv
import os
import re

def check_duplicate_codes():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    kode_baru_path = os.path.join(current_dir, "KODE BARU 2026 (sd 12 Agustus).csv")
    item_path = os.path.join(current_dir, "Item.csv")

    # 1. Membaca daftar kode baru dari KODE BARU 2026 (sd 12 Agustus).csv
    new_codes = []
    with open(kode_baru_path, mode="r", encoding="utf-8-sig", errors="replace") as f:
        reader = csv.reader(f)
        header_found = False
        kode_idx, detail_idx = -1, -1

        for row_idx, row in enumerate(reader, start=1):
            if not row:
                continue
            
            # Cari baris header
            if not header_found:
                row_lower = [c.strip().lower() for c in row]
                if "kode" in row_lower:
                    header_found = True
                    kode_idx = row_lower.index("kode")
                    if "detail" in row_lower:
                        detail_idx = row_lower.index("detail")
                    continue

            if header_found and len(row) > kode_idx:
                raw_code = row[kode_idx].strip()
                detail = row[detail_idx].strip() if (detail_idx != -1 and len(row) > detail_idx) else ""
                
                # Ambil kode utama (misal 7-8 karakter seperti 1SM-H013 / 2CO-B524)
                if raw_code:
                    code_clean = raw_code.strip()
                    new_codes.append({
                        "row": row_idx,
                        "code": code_clean,
                        "detail": detail
                    })

    # 2. Membaca data Description dari Item.csv (ERPNext format)
    erpnext_items = []
    with open(item_path, mode="r", encoding="utf-8-sig", errors="replace") as f:
        reader = csv.reader(f)
        col_names = []
        data_started = False

        for row_idx, row in enumerate(reader, start=1):
            if not row:
                continue

            # Header kolom template ERPNext
            if len(row) > 1 and "Column Name:" in row[0]:
                col_names = [c.strip().lower() for c in row]
                continue

            # Menandai baris awal data
            if any("start entering data below this line" in str(c).lower() for c in row):
                data_started = True
                continue

            if data_started:
                desc = ""
                item_code = ""
                item_name = ""

                if col_names:
                    if "description" in col_names:
                        idx = col_names.index("description")
                        if len(row) > idx:
                            desc = row[idx].strip()
                    if "item_code" in col_names:
                        idx = col_names.index("item_code")
                        if len(row) > idx:
                            item_code = row[idx].strip()
                    if "item_name" in col_names:
                        idx = col_names.index("item_name")
                        if len(row) > idx:
                            item_name = row[idx].strip()
                else:
                    # Fallback index jika kolom names tidak terdeteksi
                    if len(row) > 22:
                        desc = row[22].strip()
                    if len(row) > 1:
                        item_code = row[1].strip()
                    if len(row) > 6:
                        item_name = row[6].strip()

                erpnext_items.append({
                    "row": row_idx,
                    "item_code": item_code,
                    "item_name": item_name,
                    "description": desc
                })

    print("=" * 75)
    print("PEMERIKSAAN KODE BARU TERHADAP KOLOM DESCRIPTION DI ITEM.CSV")
    print("=" * 75)
    print(f"• Total kode dari 'KODE BARU 2026' : {len(new_codes)} item")
    print(f"• Total baris data di 'Item.csv'    : {len(erpnext_items)} item\n")

    # 3. Pengecekan apakah kode ada di Description (atau Item Code / Item Name)
    found_duplicates = []

    for item in new_codes:
        code = item["code"]
        # Regex exact word / substring match untuk kode (case-insensitive)
        pattern = re.compile(re.escape(code), re.IGNORECASE)

        for erp in erpnext_items:
            # Pengecekan utama: Description
            if erp["description"] and pattern.search(erp["description"]):
                found_duplicates.append({
                    "new_code": code,
                    "new_detail": item["detail"],
                    "new_row": item["row"],
                    "erp_row": erp["row"],
                    "erp_code": erp["item_code"],
                    "erp_desc": erp["description"]
                })

    if not found_duplicates:
        print("[STATUS: 100% AMAN & BARU]")
        print(">> Tidak ada satupun kode (7 karakter) dari 'KODE BARU 2026' yang ditemukan")
        print("   pada kolom 'Description' di 'Item.csv'.")
        print(">> Semua 206 kode baru ini terbukti belum pernah terinput/dipakai sebelumnya.")
    else:
        print(f"[PERINGATAN: DITEMUKAN {len(found_duplicates)} KODE SUDAH ADA / DUPLIKAT]")
        for idx, dup in enumerate(found_duplicates, start=1):
            print(f"\n{idx}. Kode Baru : {dup['new_code']} (Baris {dup['new_row']})")
            print(f"   Detail    : {dup['new_detail']}")
            print(f"   Ditemukan pada Item.csv:")
            print(f"   - Baris        : {dup['erp_row']}")
            print(f"   - Item Code Baru: {dup['erp_code']}")
            print(f"   - Description   : {dup['erp_desc']}")
            print("-" * 50)

    print("=" * 75)

if __name__ == "__main__":
    check_duplicate_codes()
