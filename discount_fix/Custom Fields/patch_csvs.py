import csv
import glob
import os

old_fields = [
    'custom_applied_discount',
    'custom_palma_global_disc_type',
    'custom_palma_global_disc_value',
    'custom_apply_global_discount',
    'custom_user_rate',
    'custom_user_discount_type',
    'custom_user_discount_value',
    'custom_custom_discount',
    'custom_palma_base_rate',
    'custom_palma_discount_type',
    'custom_palma_discount_amount'
]

def make_row(label, ftype, name, options='', permlevel='1'):
    r = [''] * 51
    r[0] = '0' # is_system_generated
    r[1] = label
    r[2] = ftype
    r[3] = name
    r[20] = options
    r[26] = permlevel
    r[50] = '1'
    return r

new_item_fields = [
    make_row('Palma Base Rate', 'Currency', 'custom_palma_base_rate'),
    make_row('Palma Discount Type', 'Select', 'custom_palma_discount_type', 'Percentage\nAmount'),
    make_row('Palma Discount Amount', 'Currency', 'custom_palma_discount_amount')
]

new_header_fields = [
    make_row('Palma Global Disc Type', 'Select', 'custom_palma_global_disc_type', 'Percentage\nAmount'),
    make_row('Palma Global Disc Value', 'Currency', 'custom_palma_global_disc_value')
]

for file_path in glob.glob('Custom Fields - Purchase*.csv'):
    is_item = 'Item' in file_path
    
    with open(file_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        rows = list(reader)
    
    new_rows = []
    
    # Process rows
    for r in rows:
        # Check if this row is one of the old fields
        # Note: fieldname is at index 3, but header rows might have fewer columns or different layout
        # Let's ensure the row is long enough
        if len(r) > 27 and r[3] in old_fields:
            # Set Hidden to '1'
            r[27] = '1'
            print(f"Hiding {r[3]} in {os.path.basename(file_path)}")
        
        new_rows.append(r)
        
        # If we find the insertion point, append new fields right after
        # For item: after 'qty'
        if is_item and len(r) > 3 and r[3] == 'qty':
            # Check if we already inserted them to prevent duplicates if script runs multiple times
            # Let's just insert
            print(f"Inserting new item fields after 'qty' in {os.path.basename(file_path)}")
            new_rows.extend(new_item_fields)
            
        # For header: after 'apply_discount_on'
        if not is_item and len(r) > 3 and r[3] == 'apply_discount_on':
            print(f"Inserting new header fields after 'apply_discount_on' in {os.path.basename(file_path)}")
            new_rows.extend(new_header_fields)
            
    # Write back
    with open(file_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f, quoting=csv.QUOTE_ALL)
        writer.writerows(new_rows)
        
print("Done modifying CSV files.")
