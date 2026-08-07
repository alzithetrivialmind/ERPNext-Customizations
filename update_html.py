import os
import glob

replacements = {
    'custom_custom_base_rate': 'custom_palma_base_rate',
    'custom_custom_discount_type': 'custom_palma_discount_type',
    'custom_new_custom_discount': 'custom_palma_discount_amount',
    'custom_new_global_discount_type': 'custom_palma_global_disc_type',
    'custom_new_global_discount_value': 'custom_palma_global_disc_value'
}

for root, dirs, files in os.walk(r'c:\Users\PC\Downloads\ERPNext\ERPNext Customizations\ERPNext-Customizations\Print Format'):
    for file in files:
        if file.endswith('.html'):
            filepath = os.path.join(root, file)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            new_content = content
            for old, new in replacements.items():
                new_content = new_content.replace(old, new)
                
            if new_content != content:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f"Updated HTML file {filepath}")

print("HTML update complete.")
