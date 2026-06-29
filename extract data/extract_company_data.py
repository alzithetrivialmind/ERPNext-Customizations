#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import csv
import re

def clean_company_name(name):
    """
    Cleans and standardizes company names into ALL CAPS with no punctuation.
    Examples:
        - "Palma, PT" -> "PT PALMA"
        - "PT. MAJU PRIMA JAYA" -> "PT MAJU PRIMA JAYA"
        - "HOCK SENG HOE METAL COMPANY PTE LTD" -> "HOCK SENG HOE METAL COMPANY PTE LTD"
        - "NAM LEONG CO., PTE LTD" -> "NAM LEONG CO PTE LTD"
    """
    if not name:
        return ""
    
    # 1. Convert entire name to uppercase and strip whitespace/trash chars
    name = name.upper().strip().strip(",-~: ")
    
    # 2. Standardize PT prefix/suffix
    name = re.sub(r'[,.\s]+P\.?T\.?\b', ' PT', name)
    name = re.sub(r'\bP\.?T\.?\s*$', 'PT', name)
    
    # Move PT to the front if it's at the end
    if name.endswith('PT'):
        name = "PT " + name[:-2].strip()
        
    # Standardize any internal PT/P.T.
    name = re.sub(r'\bP\.?T\.?\b', 'PT', name)
    
    # Ensure there is exactly one space after PT at the front
    if name.startswith('PT'):
        name = "PT " + name[2:].strip()
        
    # 3. Standardize PTE LTD
    name = re.sub(r'\bP\.?T\.?E\.?\s*L\.?T\.?D\.?\b', 'PTE LTD', name)
    
    # 4. Remove all dots and commas from the entire company name
    name = name.replace(".", "").replace(",", "")
    
    # 5. Clean up multiple spaces
    name = re.sub(r'\s+', ' ', name).strip()
    return name

def parse_line(line):
    """
    Parses a single messy line of company/rate data.
    """
    if not line:
        return {}
    
    original = line.strip()
    # Check for empty or generic info notes
    if not original or original.lower() in [
        "tidak ditemukan", 
        "tidak ketemu nilai adjinnya dari pembelian yang mana", 
        "data ngaco", 
        "tidak ditemukan,", 
        "tidak ketemu"
    ]:
        return {
            "Original Text": original,
            "Error/Note": original.upper(),
            "Ref Code": "",
            "Internal Company": "",
            "Vendor / Supplier": "",
            "Transaction Details": "",
            "Foreign Currency": "",
            "Foreign Rate": "",
            "Exchange Rate": ""
        }
        
    remaining = original
    # Clean prefix
    remaining = re.sub(r'^[~:\s]+', '', remaining).strip()
    
    ref_code = ""
    internal_co = ""
    
    # 1. Extract PPS Reference & Internal Company
    pps_match = re.match(r'^(PPS\s+[^~]+)~(.*?):', remaining, re.IGNORECASE)
    if pps_match:
        ref_code = pps_match.group(1).strip()
        internal_co = clean_company_name(pps_match.group(2))
        remaining = remaining[pps_match.end():].strip()
    
    # Clean remaining prefix again
    remaining = re.sub(r'^[~:\s]+', '', remaining).strip()
    
    # 2. Extract Rate & Exchange Rate Information
    # Regex allows optional currency prefix for foreign and/or exchange rate, and supports 's/S' multiplier typo.
    rate_pattern = r'((?:US\$|S\$|SGD|Rp\.|RP)?\s*[\d,\.\s]+(?:,-)?)\s+[xXsS]\s+((?:US\$|S\$|SGD|Rp\.|RP)?\s*[\d,\.\s]+(?:,-)?)'
    rate_match = re.search(rate_pattern, remaining, re.IGNORECASE)
    
    rate_info = ""
    foreign_currency = ""
    foreign_rate = ""
    exchange_rate = ""
    text_parts = []
    
    def clean_number(num_str):
        # strip trailing ,-
        cleaned = re.sub(r',-$', '', num_str.strip()).strip()
        # strip currency prefix
        cleaned = re.sub(r'^(?:US\$|S\$|SGD|Rp\.|RP)\s*', '', cleaned, flags=re.IGNORECASE).strip()
        cleaned = cleaned.replace(" ", "")
        if "," in cleaned and "." in cleaned:
            # e.g., "9,526.83" -> "9526.83"
            cleaned = cleaned.replace(",", "")
        elif "," in cleaned:
            comma_parts = cleaned.split(",")
            # Indonesian decimal style: "74,25" -> "74.25"
            if len(comma_parts) == 2 and len(comma_parts[1]) <= 2:
                cleaned = cleaned.replace(",", ".")
            else:
                cleaned = cleaned.replace(",", "")
        elif cleaned.count(".") > 1:
            # Indonesian thousands dot style: "2.139.00" -> "2139.00"
            dot_parts = cleaned.split(".")
            cleaned = "".join(dot_parts[:-1]) + "." + dot_parts[-1]
        return cleaned
        
    if rate_match:
        rate_info = rate_match.group(0).strip()
        before_rate = remaining[:rate_match.start()].strip()
        after_rate = remaining[rate_match.end():].strip()
        
        if before_rate:
            text_parts.append(before_rate)
        if after_rate:
            text_parts.append(after_rate)
            
        raw_foreign = rate_match.group(1).strip()
        raw_exchange = rate_match.group(2).strip()
        
        if "us$" in raw_foreign.lower():
            foreign_currency = "USD"
        elif "s$" in raw_foreign.lower() or "sgd" in raw_foreign.lower():
            foreign_currency = "SGD"
        elif "rp" in raw_foreign.lower():
            foreign_currency = "IDR"
        else:
            foreign_currency = "UNKNOWN"
            
        try:
            foreign_rate = clean_number(raw_foreign)
            exchange_rate = clean_number(raw_exchange)
        except Exception:
            pass
    else:
        # Check for single rate pattern with optional ,- at end of line
        single_rate_pattern = r'((?:US\$|S\$|SGD|Rp\.|RP)\s*[\d,\.\s]+(?:,-)?)$'
        single_match = re.search(single_rate_pattern, remaining, re.IGNORECASE)
        if single_match:
            rate_info = single_match.group(0).strip()
            before_rate = remaining[:single_match.start()].strip()
            if before_rate:
                text_parts.append(before_rate)
                
            raw_rate = single_match.group(1).strip()
            if "us$" in raw_rate.lower():
                foreign_currency = "USD"
            elif "s$" in raw_rate.lower() or "sgd" in raw_rate.lower():
                foreign_currency = "SGD"
            elif "rp" in raw_rate.lower():
                foreign_currency = "IDR"
            
            try:
                foreign_rate = clean_number(raw_rate)
                exchange_rate = "1" if foreign_currency == "IDR" else ""
            except Exception:
                pass
        else:
            text_parts.append(remaining)
        
    combined_text = " - ".join(text_parts)
    parts = []
    for p in re.split(r'[-:]', combined_text):
        p_str = p.strip().strip(", ")
        if p_str:
            parts.append(p_str)
            
    vendor = ""
    details_list = []
    
    company_keywords = re.compile(
        r'\b(PT|Pte|Ltd|Company|Hardware|Metal|Steel|Co|Jaya|Abadi|Utama|Benua|Sumber|Wessi|Kencana|Karya|Surya|Ocean|Leong|Hin|Limited|Private|Corp|Inc)\b', 
        re.IGNORECASE
    )
    
    generic_words = {
        'adj', 'adjin', 'local', 'ln', 'return', 'purch', 
        'sisa dari lapangan', 'sisa stock dari lapangan', 'stock sisa lapangan',
        'jan', 'feb', 'mar', 'apr', 'may', 'mei', 'jun', 'jul', 'aug', 'agt', 'sep', 'oct', 'okt', 'nov', 'dec', 'des',
        '2009', '2013', '2014', '2015', '2020', '2022', '2023', '2024', '2025'
    }
    
    for p in parts:
        if company_keywords.search(p) and not vendor:
            vendor = clean_company_name(p)
        else:
            p_words = set(p.lower().split())
            if not p_words.intersection(generic_words):
                details_list.append(p)
                
    if not vendor and parts:
        for p in parts:
            p_words = set(p.lower().split())
            if not p_words.intersection(generic_words):
                vendor = clean_company_name(p)
                break
        if not vendor:
            vendor = clean_company_name(parts[0])
            
    if vendor.lower() in generic_words:
        vendor = ""
        
    details = " - ".join([d for d in details_list if d.lower() != vendor.lower()]).strip(", -")
    
    return {
        "Original Text": original,
        "Ref Code": ref_code.upper(),
        "Internal Company": internal_co,
        "Vendor / Supplier": vendor,
        "Transaction Details": details.upper(),
        "Foreign Currency": foreign_currency.upper(),
        "Foreign Rate": foreign_rate,
        "Exchange Rate": exchange_rate,
        "Error/Note": ""
    }

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_path = os.path.join(script_dir, "EQ - Item to import.csv")
    output_path = os.path.join(script_dir, "Cleaned_Item_to_import.csv")
    
    if not os.path.exists(input_path):
        print(f"Error: Input file not found at {input_path}")
        return
        
    print(f"Reading from: {input_path}")
    print("Parsing rows and formatting company names...")
    
    rows_written = 0
    with open(input_path, "r", encoding="utf-8") as infile:
        reader = csv.reader(infile)
        header = next(reader)
        
        # Output columns
        fieldnames = [
            "Original Text",
            "Ref Code",
            "Internal Company",
            "Vendor / Supplier",
            "Transaction Details",
            "Foreign Currency",
            "Foreign Rate",
            "Exchange Rate",
            "Error/Note"
        ]
        
        # Try to open output path, fall back to numbered version if locked
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
                if counter > 20: # fail safe
                    print(f"Error: Could not write to output file. Too many lock conflicts.")
                    return
                    
        with outfile:
            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for row in reader:
                if not row:
                    continue
                parsed = parse_line(row[0])
                writer.writerow(parsed)
                rows_written += 1
                
        print(f"Success! Cleaned data written to: {fallback_path}")
        if fallback_path != output_path:
            print(f"Note: The original file was locked, so it was saved to the fallback path above.")
        print(f"Total rows processed: {rows_written}")

if __name__ == "__main__":
    main()
