# ==========================================
# SERVER SCRIPT
# Script Type: API
# API Method: create_item_from_groups_v2
# Enabled: Yes
# ==========================================

def get_group_doc(group_name: str):
	return frappe.get_doc('Item Group', group_name)


def parse_code_generic(name, level_name):
	"""
	Extract code from Item Group name by taking characters before first space.
	Format: 'CODE - Description' or 'CODE-Description' -> 'CODE'
	
	Examples:
	  'SM - Steel Material' -> 'SM'
	  'A01 - Angle Bar' -> 'A01'
	  'AB01 - Some Item' -> 'AB01'
	  '000 - No Brand' -> '000'
	
	Validation:
	  - Maximum 4 characters (alphanumeric)
	  - Any combination of letters and digits allowed
	  - Converted to uppercase
	"""
	if not name:
		return None
	
	# Split by first space to get the code part
	code = name.split(' ', 1)[0].strip()
	
	if not code:
		return None
	
	# Remove any non-alphanumeric characters and convert to uppercase
	clean_code = ''.join(c.upper() for c in code if c.isalnum())
	
	# Validate: 1-4 alphanumeric characters
	if len(clean_code) >= 1 and len(clean_code) <= 4:
		return clean_code
	
	return None

def parse_l1_code(l1_name):
	"""Extract code from Level 1 name (max 4 chars, any alphanumeric combination)"""
	return parse_code_generic(l1_name, 'Level 1')

def parse_l2_code(l2_name):
	"""Extract code from Level 2 name (max 4 chars, any alphanumeric combination)"""
	return parse_code_generic(l2_name, 'Level 2')

def parse_l3_code(l3_name):
	"""Extract code from Level 3 name (max 4 chars, any alphanumeric combination)"""
	return parse_code_generic(l3_name, 'Level 3')

# The core logic is wrapped in a function for clarity.
def run_item_creation(args):
	l1 = args.get('l1')
	l2 = args.get('l2')
	l3 = args.get('l3')
	variant_code = args.get('variant_code')
	item_name = args.get('item_name')
	stock_uom = args.get('stock_uom')
	maintain_stock = args.get('maintain_stock')
	description = args.get('description')

	if not (l1 and l2 and l3):
		raise frappe.ValidationError(_('Pilih Level 1 → Level 2 → Level 3 terlebih dahulu.'))

	# Validasi parent chain
	l2_doc = get_group_doc(l2)
	l3_doc = get_group_doc(l3)
	if l2_doc.parent_item_group != l1:
		msg = 'Group Level 2 bukan anak dari Level 1. Nilai sekarang: ' + l2 + ' → parent ' + l2_doc.parent_item_group
		raise frappe.ValidationError(_(msg))
	if l3_doc.parent_item_group != l2:
		msg = 'Group Level 3 bukan anak dari Level 2. Nilai sekarang: ' + l3 + ' → parent ' + l3_doc.parent_item_group
		raise frappe.ValidationError(_(msg))

	# Parsing kode dari "nama" Item Group
	code_l1 = parse_l1_code(l1)
	code_l2 = parse_l2_code(l2)
	code_l3 = parse_l3_code(l3)
	
	if not code_l1:
		raise frappe.ValidationError(_('Level 1 tidak sesuai format. Format: "KODE - Deskripsi" (KODE max 4 karakter alphanumeric). Contoh: "SM - Steel Material"'))
	if not code_l2:
		raise frappe.ValidationError(_('Level 2 tidak sesuai format. Format: "KODE - Deskripsi" (KODE max 4 karakter alphanumeric). Contoh: "AB - Angle Bar", "A01 - Some Item"'))
	if not code_l3:
		raise frappe.ValidationError(_('Level 3 tidak sesuai format. Format: "KODE - Deskripsi" (KODE max 4 karakter alphanumeric). Contoh: "000 - No Brand", "A001 - Brand A"'))

	# Variant: 3 digits + optional single trailing letter
	# Remove non-alphanumeric characters and convert to uppercase
	vc_chars = []
	for char in (variant_code or ''):
		if char.isalnum():
			vc_chars.append(char.upper())
	vc = ''.join(vc_chars)
	
	# Parse: digits followed by optional letter
	if not vc:
		raise frappe.ValidationError(_('(Variant Code) masukkan 3 digit angka, opsional 1 huruf di belakang.'))
	
	digit_chars = []
	letter = ''
	for char in vc:
		if char.isdigit():
			digit_chars.append(char)
		elif char.isalpha() and len(digit_chars) == 0:
			# Letter before digits - invalid
			raise frappe.ValidationError(_('(Variant Code) harus dimulai dengan angka.'))
		elif char.isalpha() and len(letter) == 0:
			# First letter after digits
			letter = char
		else:
			# More than 1 letter - invalid
			raise frappe.ValidationError(_('(Variant Code) hanya boleh 1 huruf di belakang angka.'))
	
	digits = ''.join(digit_chars)
	if not digits or len(digits) > 3:
		raise frappe.ValidationError(_('(Variant Code) masukkan 1-3 digit angka.'))
	
	# Pad digits to 3 characters
	digits = digits.zfill(3)
	variant = digits + letter

	base_code = code_l1 + '-' + code_l2 + '-' + code_l3
	item_code = base_code + variant

	if not stock_uom:
		raise frappe.ValidationError(_('Stock UoM wajib diisi.'))
	final_item_name = item_name or item_code

	# Cek duplikasi
	if frappe.db.exists('Item', {'item_code': item_code}):
		msg = 'Item dengan kode ' + item_code + ' sudah pernah dibuat. Silakan gunakan variant code yang berbeda.'
		frappe.throw(
			msg=_(msg),
			title=_('Item Sudah Ada'),
			exc=frappe.DuplicateEntryError
		)

	# Create new item document
	item = frappe.get_doc({
		'doctype': 'Item',
		'item_code': item_code,
		'item_name': final_item_name,
		'description': description or '',
		'stock_uom': stock_uom,
		'is_stock_item': int(maintain_stock or 0),
		'item_group': l3
	})
	
	item.flags.ignore_mandatory = False
	item.insert()
	frappe.db.commit()

	return {'item_name': item.name, 'item_code': item.item_code, 'base_code': base_code}


# Main execution block for Server Script API
result = run_item_creation(frappe.form_dict)
frappe.response['message'] = result
