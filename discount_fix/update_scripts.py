import os
import glob

replacements = {
    'custom_palma_base_rate': 'custom_palma_base_rate',
    'custom_palma_discount_type': 'custom_palma_discount_type',
    'custom_palma_discount_amount': 'custom_palma_discount_amount',
    'custom_palma_global_disc_type': 'custom_palma_global_disc_type',
    'custom_palma_global_disc_value': 'custom_palma_global_disc_value'
}

for root, dirs, files in os.walk(r'c:\Users\PC\Downloads\ERPNext\ERPNext Customizations\ERPNext-Customizations\discount_fix'):
    for file in files:
        if file.endswith('.py') or file.endswith('.js'):
            filepath = os.path.join(root, file)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            new_content = content
            for old, new in replacements.items():
                new_content = new_content.replace(old, new)
                
            if new_content != content:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f"Updated {filepath}")
