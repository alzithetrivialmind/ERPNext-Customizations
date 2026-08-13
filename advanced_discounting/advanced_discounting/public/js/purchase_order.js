// ==========================================
// Advanced Discounting — Purchase Order Client Script
// Loaded via app_include_js in hooks.py
// ==========================================

frappe.ui.form.on("Purchase Order Item", {
    item_code: function(frm, cdt, cdn) {
        // Asynchronous price_list_rate fetch will sync to custom_palma_base_rate
    },

    // Direction B: ERPNext price_list_rate → custom_palma_base_rate
    price_list_rate: function(frm, cdt, cdn) {
        let row = frappe.get_doc(cdt, cdn);
        let new_plr = flt(row.price_list_rate);
        let cur_cbr = flt(row.custom_palma_base_rate);

        if (new_plr > 0 && Math.abs(new_plr - cur_cbr) > 0.001) {
            frappe.model.set_value(cdt, cdn, "custom_palma_base_rate", new_plr);
        }
    },

    // Direction A: custom_palma_base_rate → price_list_rate
    custom_palma_base_rate: function(frm, cdt, cdn) {
        frm.events.calculate_row_discount(frm, cdt, cdn);
    },
    custom_palma_discount_type: function(frm, cdt, cdn) {
        frm.events.calculate_row_discount(frm, cdt, cdn);
    },
    custom_palma_discount_amount: function(frm, cdt, cdn) {
        frm.events.calculate_row_discount(frm, cdt, cdn);
    },
    qty: function(frm, cdt, cdn) {
        frm.events.calculate_row_discount(frm, cdt, cdn);
    }
});


frappe.ui.form.on("Purchase Order", {
    onload: function(frm) {
        frm.events.ensure_fields_visible(frm);
    },
    refresh: function(frm) {
        frm.events.ensure_fields_visible(frm);
    },
    ensure_fields_visible: function(frm) {
        frm.set_df_property("custom_sec_palma_discount", "hidden", 0);
        frm.set_df_property("custom_palma_global_disc_type", "hidden", 0);
        frm.set_df_property("custom_palma_global_disc_value", "hidden", 0);
        frm.set_df_property("custom_apply_global_discount", "hidden", 0);
    },
    custom_apply_global_discount: function(frm) {
        frm.events.apply_global_discount(frm);
    },

    apply_global_discount: function(frm) {
        let dtype = frm.doc.custom_palma_global_disc_type;
        let dval  = flt(frm.doc.custom_palma_global_disc_value);

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

        if (dtype === "Percentage") {
            items.forEach(function(row) {
                frappe.model.set_value(row.doctype, row.name, "custom_palma_discount_type", dtype);
                frappe.model.set_value(row.doctype, row.name, "custom_palma_discount_amount", dval);
            });
        } else if (dtype === "Amount") {
            // Amount: VALUE-WEIGHTED distribution with REMAINDER ABSORPTION on last row
            let total_amount = items.reduce(function(sum, r) {
                return sum + flt(r.custom_palma_base_rate) * flt(r.qty || 1);
            }, 0);

            if (total_amount <= 0) {
                frappe.msgprint({
                    title: "Cannot Distribute",
                    message: "Total item amount is zero. Cannot distribute Amount-type discount.",
                    indicator: "orange"
                });
                return;
            }

            let allocated_so_far = 0.0;
            items.forEach(function(row, idx) {
                let per_row_discount = 0.0;
                if (idx === items.length - 1) {
                    // Absorbs exact remainder on last item row to prevent FP drift
                    per_row_discount = flt(dval - allocated_so_far, 2);
                } else {
                    let row_amount = flt(row.custom_palma_base_rate) * flt(row.qty || 1);
                    per_row_discount = flt(dval * (row_amount / total_amount), 2);
                    allocated_so_far += per_row_discount;
                }
                frappe.model.set_value(row.doctype, row.name, "custom_palma_discount_type", dtype);
                frappe.model.set_value(row.doctype, row.name, "custom_palma_discount_amount", per_row_discount);
            });
        }

        frappe.show_alert({
            message: `Global ${dtype} discount applied to ${total_rows} item(s). Click Save to finalize.`,
            indicator: "green"
        }, 5);
    },

    calculate_row_discount: function(frm, cdt, cdn) {
        let row = frappe.get_doc(cdt, cdn);
        let baseline = flt(row.custom_palma_base_rate);
        let dtype = row.custom_palma_discount_type;
        let dval = flt(row.custom_palma_discount_amount);
        let qty = flt(row.qty) || 1.0;

        let discount_amt = 0.0;
        if (dtype === "Percentage") {
            discount_amt = baseline * (dval / 100.0);
        } else if (dtype === "Amount") {
            discount_amt = dval / qty;
        }

        let final_rate = baseline - discount_amt;
        if (final_rate < 0) {
            final_rate = 0.0;
            discount_amt = baseline;
        }

        frappe.model.set_value(cdt, cdn, "price_list_rate", baseline);
        frappe.model.set_value(cdt, cdn, "discount_amount", discount_amt);
        if (baseline > 0) {
            frappe.model.set_value(cdt, cdn, "discount_percentage", (discount_amt / baseline) * 100.0);
        } else {
            frappe.model.set_value(cdt, cdn, "discount_percentage", 0.0);
        }
        frappe.model.set_value(cdt, cdn, "rate", final_rate);
    }
});
