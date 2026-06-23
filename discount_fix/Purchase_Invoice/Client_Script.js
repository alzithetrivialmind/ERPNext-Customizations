// ==========================================
// CLIENT SCRIPT
// DocType        : Purchase Invoice
// Apply To       : Form
// ==========================================


// -----------------------------------------------------------
// PART 1: Auto-fill custom_custom_base_rate when an item is selected
// -----------------------------------------------------------
frappe.ui.form.on("Purchase Invoice Item", {
    item_code: function(frm, cdt, cdn) {
        let row = frappe.get_doc(cdt, cdn);
        if (row.item_code && !row.custom_custom_base_rate) {
            setTimeout(() => {
                let updated_row = frappe.get_doc(cdt, cdn);
                if (updated_row.price_list_rate) {
                    frappe.model.set_value(cdt, cdn, "custom_custom_base_rate", updated_row.price_list_rate);
                }
            }, 300);
        }
    }
});


// -----------------------------------------------------------
// PART 2: Global Discount — Apply to All Items button
// -----------------------------------------------------------
frappe.ui.form.on("Purchase Invoice", {
    refresh: function(frm) {
        frm.add_custom_button("Apply Global Discount to All Items", function() {

            let dtype = frm.doc.custom_new_global_discount_type;
            let dval  = flt(frm.doc.custom_new_global_discount_value);

            if (!dtype) {
                frappe.msgprint({
                    title: "Missing Input",
                    message: "Please select a Global Discount Type (Percentage or Amount) first.",
                    indicator: "orange"
                });
                return;
            }

            if (!dval || dval <= 0) {
                frappe.msgprint({
                    title: "Missing Input",
                    message: "Please enter a Global Discount Value greater than 0.",
                    indicator: "orange"
                });
                return;
            }

            let items = frm.doc.items;
            if (!items || items.length === 0) {
                frappe.msgprint({
                    title: "No Items",
                    message: "There are no items in this document yet.",
                    indicator: "orange"
                });
                return;
            }

            let total_rows = items.length;

            items.forEach(function(row) {
                frappe.model.set_value(row.doctype, row.name, "custom_custom_discount_type", dtype);

                if (dtype === "Percentage") {
                    frappe.model.set_value(row.doctype, row.name, "custom_new_custom_discount", dval);
                } else if (dtype === "Amount") {
                    let per_row_discount = flt(dval / total_rows);
                    frappe.model.set_value(row.doctype, row.name, "custom_new_custom_discount", per_row_discount);
                }
            });

            frappe.show_alert({
                message: `Global ${dtype} discount applied to ${total_rows} item(s). Click Save to finalize.`,
                indicator: "green"
            }, 5);

        }, "Discount");
    }
});
