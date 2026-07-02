#!/usr/bin/env python
# -*- coding: utf-8 -*-

import csv
import os
import datetime

def to_float(val):
    if not val:
        return 0.0
    val = val.strip().replace(",", "")
    try:
        return float(val)
    except ValueError:
        return 0.0

def parse_date(date_str):
    if not date_str:
        return ""
    date_str = date_str.strip()
    if date_str.isdigit():
        # Excel serial date
        serial = int(date_str)
        try:
            dt = datetime.datetime(1899, 12, 30) + datetime.timedelta(days=serial)
            return dt.strftime("%m/%d/%Y")
        except Exception:
            return ""
    import re
    if re.search(r'[a-zA-Z]', date_str):
        return ""
    return date_str

def get_month_info(month_str):
    month_map = {
        "jan": (1, "January"),
        "feb": (2, "February"),
        "mar": (3, "March"),
        "apr": (4, "April"),
        "may": (5, "May"),
        "mei": (5, "May"),
        "jun": (6, "June"),
        "jul": (7, "July"),
        "aug": (8, "August"),
        "agt": (8, "August"),
        "sep": (9, "September"),
        "oct": (10, "October"),
        "okt": (10, "October"),
        "nov": (11, "November"),
        "dec": (12, "December"),
        "des": (12, "December")
    }
    if not month_str:
        return None, ""
    m_clean = month_str.strip().lower()[:3]
    return month_map.get(m_clean, (None, month_str.strip()))

def normalize_currency(curr):
    curr = curr.strip().upper()
    if "US" in curr:
        return "USD"
    if "S$" in curr or "SGD" in curr:
        return "SGD"
    if "RP" in curr or "IDR" in curr:
        return "IDR"
    return curr

def format_decimal(val, decimals_to_keep=2):
    # Cukup bulatkan dan jadikan string, Excel tidak suka banyak trailing zero (dibaca sebagai text)
    return str(round(val, decimals_to_keep))

def clean_company_name(name):
    if not name:
        return ""
    import re
    name = name.upper().strip().strip(",-~: ")
    name = re.sub(r'[,.\s]+P\.?T\.?\b', ' PT', name)
    name = re.sub(r'\bP\.?T\.?\s*$', 'PT', name)
    if name.endswith('PT'):
        name = "PT " + name[:-2].strip()
    name = re.sub(r'\bP\.?T\.?\b', 'PT', name)
    if name.startswith('PT'):
        name = "PT " + name[2:].strip()
    name = re.sub(r'\bP\.?T\.?E\.?\s*L\.?T\.?D\.?\b', 'PTE LTD', name)
    name = name.replace(".", "").replace(",", "")
    name = re.sub(r'\s+', ' ', name).strip()
    return name

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_path = os.path.join(script_dir, "SM - Sudah dikasih ke Alzi - Sorted unfiltered.csv")
    output_path = os.path.join(script_dir, "Items to Import SR data.csv")
    
    if not os.path.exists(input_path):
        print(f"Error: Input file not found at {input_path}")
        return
        
    print(f"Reading from: {input_path}")
    
    headers = [
        ["Bulk Edit Items"] + [""] * 44,
        ["Barcode", "Has Item Scanned", "Item Code", "Item Name", "Item Group", "Warehouse", "Quantity", "Stock UOM", "Valuation Rate", "Amount", "Allow Zero Valuation Rate", "Use Serial No / Batch Fields", "Reconcile All Serial Nos / Batches", "Serial / Batch Bundle", "Current Serial / Batch Bundle", "Serial No", "", "Batch No", "Current Qty", "Current Amount", "Current Valuation Rate", "Current Serial No", "Quantity Difference", "Amount Difference", "SR Tanggal RIO", "SR No RIO", "SR Tanggal RDO", "SR No RDO", "SR Supplier Historis", "SR Transaction Type", "SR Qty Invoice", "SR Supplier Currency", "SR Harga Supplier", "SR Total dari Supplier", "SR Kurs ke IDR", "SR Kurs ke USD", "SR Total in USD", "SR No PIB", "SR Tahun PIB", "SR Bulan PIB", "SR Tanggal PIB", "SR Kurs pada PIB", "SR No Invoice Vendor", "SR Tahun doc RDO", "SR Kode Lama"],
        ["barcode", "has_item_scanned", "item_code", "item_name", "item_group", "warehouse", "qty", "stock_uom", "valuation_rate", "amount", "allow_zero_valuation_rate", "use_serial_batch_fields", "reconcile_all_serial_batch", "serial_and_batch_bundle", "current_serial_and_batch_bundle", "serial_no", "", "batch_no", "current_qty", "current_amount", "current_valuation_rate", "current_serial_no", "quantity_difference", "amount_difference", "custom_sr_tanggal_rio", "custom_sr_no_rio", "custom_sr_tanggal_rdo", "custom_sr_no_rdo", "custom_sr_supplier_historis", "custom_sr_transaction_type", "custom_sr_qty_invoice", "custom_sr_supplier_currency", "custom_sr_harga_supplier", "custom_sr_total_dari_supplier", "custom_sr_kurs_ke_idr", "custom_sr_kurs_ke_usd", "custom_sr_total_in_usd", "custom_sr_no_pib", "custom_sr_tahun_pib", "custom_sr_bulan_pib", "custom_sr_tanggal_pib", "custom_sr_kurs_pada_pib", "custom_sr_no_invoice_vendor", "custom_sr_tahun_doc_rdo", "custom_sr_kode_lama"],
        ["", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "mm/dd/yyyy", "", "mm/dd/yyyy", "", "", "", "", "", "", "", "", "", "", "", "", "", "mm/dd/yyyy", "", "", "", ""],
        ["The CSV format is case sensitive"] + [""] * 44,
        ["Do not edit headers which are preset in the template"] + [""] * 44,
        ["------"] + [""] * 44
    ]
    
    rows_written = 0
    with open(input_path, "r", encoding="utf-8") as infile:
        reader = csv.reader(infile)
        src_header = next(reader)
        
        output_rows = list(headers)
        
        for row in reader:
            if not row or not any(row):
                continue
            
            countif = row[3].strip()
            item_code = row[6].strip()
            # Skip row if item code is 'Data Tidak Ada'
            if item_code.lower() == "data tidak ada":
                continue

            item_name = row[9].strip()
            item_group = row[10].strip()
            warehouse = "Stores - PPS"
            qty = to_float(row[16])
            
            # Selalu gunakan amount_raw (Kolom AC) sebagai Amount agar 100% match
            amount_raw = to_float(row[28])
            amount = amount_raw
            
            # Hitung valuation_rate dari amount_raw agar tidak terjadi rounding difference saat di-import
            if qty > 0:
                valuation_rate = amount / qty
            else:
                valuation_rate = amount
            
            tx_type = row[15].strip()
            if not tx_type or tx_type.lower() == "tidak ditemukan":
                tx_type = "ADJUSTMENT"
            batch_name = f"{countif} - {item_code} - {tx_type}" if (countif and item_code and tx_type) else ""
            
            pib_year = row[36].strip()
            pib_month_raw = row[37].strip()
            pib_day = row[38].strip()
            month_num, month_name = get_month_info(pib_month_raw)
            
            if pib_year and month_num and pib_day:
                try:
                    day_int = int(pib_day)
                    year_int = int(pib_year)
                    custom_sr_tanggal_pib = f"{month_num}/{day_int}/{year_int}"
                except ValueError:
                    custom_sr_tanggal_pib = ""
            else:
                custom_sr_tanggal_pib = ""
                
            pib_val = row[35].strip()
            custom_sr_no_pib = pib_val if (pib_val and not pib_val.startswith("LOCAL-")) else ""
            
            supplier_raw = row[14].strip()
            supplier_clean = clean_company_name(supplier_raw)
            if not supplier_clean:
                supplier_clean = "ADJUSTMENT COMPANY"
            
            qty_str = str(qty)
            if qty_str.endswith(".0"):
                qty_str = qty_str[:-2]
                
            out_row = [""] * 45
            out_row[0] = "" # Barcode
            out_row[1] = "" # Has Item Scanned (Col B) - helper, now empty
            out_row[2] = item_code # Item Code
            out_row[3] = item_name # Item Name
            out_row[4] = item_group # Item Group
            out_row[5] = warehouse # Warehouse
            out_row[6] = qty_str # Qty
            out_row[7] = "" # Stock UOM
            out_row[8] = format_decimal(valuation_rate, 4) # Valuation Rate
            out_row[9] = format_decimal(amount, 2) # Amount
            out_row[10] = "" # Allow Zero Valuation Rate
            out_row[11] = "1" # Use Serial No / Batch Fields
            out_row[12] = "" # Reconcile All Serial Nos / Batches
            out_row[13] = "" # Serial / Batch Bundle
            out_row[14] = "" # Current Serial / Batch Bundle
            out_row[15] = "" # Serial No
            out_row[16] = "" # Empty header col (Col Q) - helper, now empty
            out_row[17] = batch_name # Batch No
            out_row[18] = "" # Current Qty
            out_row[19] = "" # Current Amount
            out_row[20] = "" # Current Valuation Rate
            out_row[21] = "" # Current Serial No
            out_row[22] = "" # Quantity Difference
            out_row[23] = "" # Amount Difference
            out_row[24] = parse_date(row[1]) # SR Tanggal RIO
            out_row[25] = row[2].strip() # SR No RIO
            out_row[26] = parse_date(row[11]) # SR Tanggal RDO
            out_row[27] = row[12].strip() # SR No RDO
            out_row[28] = supplier_clean # SR Supplier Historis
            out_row[29] = tx_type # SR Transaction Type
            out_row[30] = row[17].strip() # SR Qty Invoice
            out_row[31] = normalize_currency(row[18]) # SR Supplier Currency
            out_row[32] = row[19].strip() # SR Harga Supplier
            out_row[33] = row[22].strip() # SR Total dari Supplier
            out_row[34] = row[25].strip() # SR Kurs ke IDR
            out_row[35] = row[31].strip() # SR Kurs ke USD
            out_row[36] = row[34].strip() # SR Total in USD
            out_row[37] = custom_sr_no_pib # SR No PIB
            out_row[38] = pib_year # SR Tahun PIB
            out_row[39] = month_name # SR Bulan PIB
            out_row[40] = custom_sr_tanggal_pib # SR Tanggal PIB
            out_row[41] = row[39].strip() # SR Kurs pada PIB
            out_row[42] = row[40].strip() # SR No Invoice Vendor
            out_row[43] = "" # SR Tahun doc RDO
            out_row[44] = row[4].strip() # SR Kode Lama
            
            output_rows.append(out_row)
            rows_written += 1
            
    outfile = None
    fallback_path = output_path
    counter = 1
    while outfile is None:
        try:
            outfile = open(fallback_path, "w", encoding="utf-8", newline="")
        except PermissionError:
            name, ext = os.path.splitext(output_path)
            fallback_path = f"{name}_{counter}{ext}"
            counter += 1
            if counter > 20:
                print(f"Error: Could not write to output file. Too many lock conflicts.")
                return
                
    with outfile:
        writer = csv.writer(outfile)
        writer.writerows(output_rows)
        
    print(f"Success! Cleaned data written to: {fallback_path}")
    print(f"Total rows processed: {rows_written}")

if __name__ == "__main__":
    main()
