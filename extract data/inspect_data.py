import re

def clean_company_name(name):
    if not name:
        return ""
    
    # 1. Convert entire name to uppercase
    name = name.upper().strip()
    
    # Remove any start/end trash characters
    name = name.strip(",-~: ")
    
    # 2. Standardize PT prefix/suffix
    # Match any variant of PT/P.T. at the end, optionally separated by comma/space
    name = re.sub(r'[,.\s]+P\.?T\.?\b', ' PT', name)
    name = re.sub(r'\bP\.?T\.?\s*$', 'PT', name)
    
    # If ends with PT, move it to the front
    if name.endswith('PT'):
        name = "PT " + name[:-2].strip()
        
    # Standardize PT/P.T. at the beginning or middle
    name = re.sub(r'\bP\.?T\.?\b', 'PT', name)
    
    # Ensure there is exactly one space after PT if it's at the front
    if name.startswith('PT'):
        name = "PT " + name[2:].strip()
        
    # 3. Standardize PTE LTD
    name = re.sub(r'\bP\.?T\.?E\.?\s*L\.?T\.?D\.?\b', 'PTE LTD', name)
    
    # 4. Remove all dots and commas from the entire company name
    name = name.replace(".", "").replace(",", "")
    
    # 5. Clean up multiple spaces
    name = re.sub(r'\s+', ' ', name).strip()
    
    return name

test_names = [
    "Palma, PT",
    "Revalindo Utama Teknik, PT",
    "Karya Surya, PT",
    "Wessi Kencana Abadi, PT",
    "PT. MAJU PRIMA JAYA",
    "PT SUMBER STEEL JAYATAMA",
    "HOCK SENG HOE METAL COMPANY PTE LTD",
    "NAM LEONG CO., PTE LTD",
    "NAM LEONG CO. PTE LTD",
    "CHUAN LEONG METALIMPEX, CO., PTE LTD",
    "HS XPRESS PRIVATE LIMITED",
    "PT. GLOBAL BENUA BAJATAMA"
]

print("Test cleans (Caps & No punctuation):")
for name in test_names:
    print(f"Original: {repr(name)} -> {repr(clean_company_name(name))}")
