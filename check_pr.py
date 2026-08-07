import frappe
frappe.init(site="ERPNext-Customizations")
frappe.connect()
pr_meta = frappe.get_meta("Purchase Receipt")
for field in pr_meta.fields:
    if "return" in field.fieldname:
        print(field.fieldname)
