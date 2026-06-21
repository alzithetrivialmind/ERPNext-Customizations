// ==========================================
// CLIENT SCRIPT (UI ERPNext)
// DocType: Sales Invoice (atau PO, SO, dll)
// Apply To: Form
// ==========================================

frappe.ui.form.on("Sales Invoice Item", {
    item_code: function(frm, cdt, cdn) {
        let row = frappe.get_doc(cdt, cdn);

        // Jika user memilih item dan base rate masih kosong, 
        // kita tunggu sejenak agar ERPNext menarik price_list_rate standar, 
        // lalu kita copy nilainya secara instan ke custom_user_rate
        if (row.item_code && !row.custom_user_rate) {
            setTimeout(() => {
                let updated_row = frappe.get_doc(cdt, cdn);
                if (updated_row.price_list_rate) {
                    frappe.model.set_value(cdt, cdn, "custom_user_rate", updated_row.price_list_rate);
                }
            }, 300);
        }
    }
});
