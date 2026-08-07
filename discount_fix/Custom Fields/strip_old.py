import csv
import glob
import os

old_fields = [
    'custom_applied_discount',
    'custom_new_global_discount_type',
    'custom_new_global_discount_value',
    'custom_apply_global_discount',
    'custom_user_rate',
    'custom_user_discount_type',
    'custom_user_discount_value',
    'custom_custom_discount',
    'custom_custom_base_rate',
    'custom_custom_discount_type',
    'custom_new_custom_discount'
]

for file_path in glob.glob(r'c:\Users\PC\Downloads\ERPNext\ERPNext Customizations\ERPNext-Customizations\discount_fix\Custom Fields\Custom Fields - Purchase*.csv'):
    with open(file_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        rows = list(reader)
    
    new_rows = []
    removed_count = 0
    for r in rows:
        if len(r) > 3 and r[3] in old_fields:
            print(f"Removing old field {r[3]} from {os.path.basename(file_path)}")
            removed_count += 1
            continue
        new_rows.append(r)
        
    if removed_count > 0:
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f, quoting=csv.QUOTE_ALL)
            writer.writerows(new_rows)
        print(f"Removed {removed_count} fields from {os.path.basename(file_path)}")

print("Done stripping old fields.")
