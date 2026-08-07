import csv
import glob
import os

# 1. Rename in JS scripts
for root, dirs, files in os.walk(r'c:\Users\PC\Downloads\ERPNext\ERPNext Customizations\ERPNext-Customizations\discount_fix'):
    for file in files:
        if file.endswith('.js'):
            filepath = os.path.join(root, file)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            new_content = content.replace('custom_apply_global_discount', 'custom_palma_global_disc_apply')
                
            if new_content != content:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f"Updated {filepath} for button rename")

# 2. Add button to Header CSVs
def make_button_row():
    r = [''] * 51
    r[0] = '0' # is_system_generated
    r[1] = 'Apply Global Discount'
    r[2] = 'Button'
    r[3] = 'custom_palma_global_disc_apply'
    r[50] = '1'
    return r

for file_path in glob.glob(r'c:\Users\PC\Downloads\ERPNext\ERPNext Customizations\ERPNext-Customizations\discount_fix\Custom Fields\Custom Fields - Purchase*.csv'):
    if 'Item' in file_path:
        continue
        
    with open(file_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        rows = list(reader)
    
    new_rows = []
    
    for r in rows:
        new_rows.append(r)
        
        # Insert button after custom_palma_global_disc_value
        if len(r) > 3 and r[3] == 'custom_palma_global_disc_value':
            print(f"Inserting new button field after 'custom_palma_global_disc_value' in {os.path.basename(file_path)}")
            new_rows.append(make_button_row())
            
    with open(file_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f, quoting=csv.QUOTE_ALL)
        writer.writerows(new_rows)
        
# For the For Header.csv just in case
header_csv = r'c:\Users\PC\Downloads\ERPNext\ERPNext Customizations\ERPNext-Customizations\discount_fix\Custom Fields\Custom Fields - For Header.csv'
if os.path.exists(header_csv):
    with open(header_csv, 'r', newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        rows = list(reader)
    new_rows = []
    for r in rows:
        new_rows.append(r)
        if len(r) > 3 and r[3] == 'custom_palma_global_disc_value':
            print(f"Inserting new button field after 'custom_palma_global_disc_value' in For Header.csv")
            new_rows.append(make_button_row())
    with open(header_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f, quoting=csv.QUOTE_ALL)
        writer.writerows(new_rows)

print("Done patching buttons.")
