// ==========================================
// CLIENT SCRIPT
// DocType        : Purchase Order
// Apply To       : Form
// ==========================================
//
// 2-WAY SYNC LOGIC:
//   custom_custom_base_rate <--> price_list_rate
//
//   Direction A (user edits C. Base Rate):
//     custom_custom_base_rate handler → calculate_row_discount → sets price_list_rate = baseline
//
//   Direction B (ERPNext updates price_list_rate, e.g. after item_code fetch):
//     price_list_rate handler → sets custom_custom_base_rate = price_list_rate
//     This then triggers Direction A automatically.
//
//   Loop prevention: the price_list_rate handler only fires if the difference is > 0.001,
//   so after Direction A sets price_list_rate, the handler sees no difference and stops.
// ==========================================


// -----------------------------------------------------------
// PART 1: Real-time row discount calculation + 2-way sync
// -----------------------------------------------------------
frappe.ui.form.on("Purchase Order Item", {
    item_code: function(frm, cdt, cdn) {
        // When an item is selected, ERPNext will fetch price_list_rate asynchronously.
        // The price_list_rate handler below will then auto-sync to custom_custom_base_rate.
        // No setTimeout needed anymore — the sync is triggered by price_list_rate change.
    },

    // Direction B: ERPNext price_list_rate → custom_custom_base_rate
    price_list_rate: function(frm, cdt, cdn) {
        let row = frappe.get_doc(cdt, cdn);
        let new_plr = flt(row.price_list_rate);
        let cur_cbr = flt(row.custom_custom_base_rate);

        // Only sync if meaningfully different to prevent infinite loop
        if (new_plr > 0 && Math.abs(new_plr - cur_cbr) > 0.001) {
            frappe.model.set_value(cdt, cdn, "custom_custom_base_rate", new_plr);
            // This triggers the custom_custom_base_rate handler → calculate_row_discount
        }
    },

    // Direction A: custom_custom_base_rate → price_list_rate (via calculate_row_discount)
    custom_custom_base_rate: function(frm, cdt, cdn) {
        frm.events.calculate_row_discount(frm, cdt, cdn);
    },
    custom_custom_discount_type: function(frm, cdt, cdn) {
        frm.events.calculate_row_discount(frm, cdt, cdn);
    },
    custom_new_custom_discount: function(frm, cdt, cdn) {
        frm.events.calculate_row_discount(frm, cdt, cdn);
    },
    qty: function(frm, cdt, cdn) {
        frm.events.calculate_row_discount(frm, cdt, cdn);
    }
});


// -----------------------------------------------------------
// PART 2: Global Discount — Connect to inline button and apply to all rows
// -----------------------------------------------------------
frappe.ui.form.on("Purchase Order", {
    // Triggered when clicking the custom inline button in the form
    custom_apply_global_discount: function(frm) {
        frm.events.apply_global_discount(frm);
    },

    apply_global_discount: function(frm) {
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
    },

    calculate_row_discount: function(frm, cdt, cdn) {
        let row = frappe.get_doc(cdt, cdn);
        let baseline = flt(row.custom_custom_base_rate);
        let dtype = row.custom_custom_discount_type;
        let dval = flt(row.custom_new_custom_discount);
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

        // Sync Direction A: custom_custom_base_rate → price_list_rate
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
