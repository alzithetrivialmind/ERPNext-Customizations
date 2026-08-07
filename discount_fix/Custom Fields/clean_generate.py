import csv
import glob
import os
import shutil

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
    make_row('Palma Global Disc Value', 'Currency', 'custom_palma_global_disc_value'),
    # Note the label change here to avoid ERPNext's name autogeneration bug!
    make_row('Palma Global Disc Apply', 'Button', 'custom_palma_global_disc_apply')
]

out_dir = r'c:\Users\PC\Downloads\ERPNext\ERPNext Customizations\ERPNext-Customizations\discount_fix\Custom Fields\Generated'

# We only process the files that end with 'Old.csv' since these are the pure original exports
for file_path in glob.glob(r'c:\Users\PC\Downloads\ERPNext\ERPNext Customizations\ERPNext-Customizations\discount_fix\Custom Fields\* Old.csv'):
    # The output filename should not have ' Old' in it
    base_name = os.path.basename(file_path).replace(' Old', '')
    out_path = os.path.join(out_dir, base_name)
    
    is_item = 'Item' in base_name
    
    with open(file_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        rows = list(reader)
    
    new_rows = []
    
    for r in rows:
        # Strip old fields completely
        if len(r) > 3 and r[3] in old_fields:
            continue
            
        new_rows.append(r)
        
        # Insert new fields after 'qty' for items
        if is_item and len(r) > 3 and r[3] == 'qty':
            new_rows.extend(new_item_fields)
            
        # Insert new fields after 'apply_discount_on' for headers
        if not is_item and len(r) > 3 and r[3] == 'apply_discount_on':
            new_rows.extend(new_header_fields)
            
    with open(out_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f, quoting=csv.QUOTE_ALL)
        writer.writerows(new_rows)
        
    print(f"Generated clean file: {out_path}")

print("Clean generation complete.")
