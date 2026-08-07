import csv

header = ['Bulk Edit Fields'] + [''] * 50
h2 = ['Is System Generated','Label','Type','Name','Non Negative','Mandatory','Unique','Is Virtual','In List View','In Standard Filter','In Global Search','In Preview','Bold','No Copy','Allow in Quick Entry','Translatable','Link Filters','Default','Precision','Length','Options','Sort Options','Fetch From','Fetch on Save if Empty','Show Dashboard','Depends On','Perm Level','Hidden','Read Only','Collapsible','Allow Bulk Edit','Collapsible Depends On','Ignore User Permissions','Allow on Submit','Report Hide','Remember Last Selected Value','Hide Border','Ignore XSS Filter','Mandatory Depends On','Read Only Depends On','In Filter','Hide Seconds','Hide Days','Description','Placeholder','Print Hide','Print Hide If No Value','Print Width','Columns','Width','Is Custom Field']
h3 = ['is_system_generated','label','fieldtype','fieldname','non_negative','reqd','unique','is_virtual','in_list_view','in_standard_filter','in_global_search','in_preview','bold','no_copy','allow_in_quick_entry','translatable','link_filters','default','precision','length','options','sort_options','fetch_from','fetch_if_empty','show_dashboard','depends_on','permlevel','hidden','read_only','collapsible','allow_bulk_edit','collapsible_depends_on','ignore_user_permissions','allow_on_submit','report_hide','remember_last_selected_value','hide_border','ignore_xss_filter','mandatory_depends_on','read_only_depends_on','in_filter','hide_seconds','hide_days','description','placeholder','print_hide','print_hide_if_no_value','print_width','columns','width','is_custom_field']
h4 = [' '] * 51
h4[18] = 'Set non-standard precision for a Float or Currency field '
h4[20] = 'For Links, enter the DocType as range.\nFor Select, enter list of Options, each on a new line. '
h4[23] = 'If unchecked, the value will always be re-fetched on save. '
h4[25] = 'This field will appear only if the fieldname defined here has value OR the rules are true (examples):\nmyfield\neval:doc.myfield==\'My Value\'\neval:doc.age>18 '
h4[37] = 'Don\'t encode HTML tags like <script> or just characters like < or >, as they could be intentionally used in this field '
h4[47] = 'Print Width of the field, if the field is a column in a table '
h4[48] = 'Number of columns for a field in a Grid (Total Columns in a grid should be less than 11) '

def make_row(label, ftype, name, options='', permlevel='1'):
    r = [''] * 51
    r[0] = '0'
    r[1] = label
    r[2] = ftype
    r[3] = name
    r[20] = options
    r[26] = permlevel
    r[50] = '1'
    return r

items = [
    make_row('Palma Base Rate', 'Currency', 'custom_palma_base_rate'),
    make_row('Palma Discount Type', 'Select', 'custom_palma_discount_type', 'Percentage\nAmount'),
    make_row('Palma Discount Amount', 'Currency', 'custom_palma_discount_amount')
]

headers = [
    make_row('Palma Global Disc Type', 'Select', 'custom_palma_global_disc_type', 'Percentage\nAmount'),
    make_row('Palma Global Disc Value', 'Currency', 'custom_palma_global_disc_value')
]

def write_csv(filename, rows):
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f, quoting=csv.QUOTE_ALL)
        writer.writerow(header)
        writer.writerow(h2)
        writer.writerow(h3)
        writer.writerow(h4)
        writer.writerow(['The CSV format is case sensitive'] + ['']*50)
        writer.writerow(['Do not edit headers which are preset in the template'] + ['']*50)
        writer.writerow(['------'] + ['']*50)
        # Adding empty padding for options that don't have exactly 51 columns
        # However csv writer handles it fine if we just provide the list
        for r in rows:
            writer.writerow(r)

write_csv('Custom Fields - For Item.csv', items)
write_csv('Custom Fields - For Header.csv', headers)
