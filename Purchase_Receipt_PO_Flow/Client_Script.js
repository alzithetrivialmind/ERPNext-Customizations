// Script Name: PR - Custom PO Flow (Final)
// Doctype: Purchase Receipt

function show_pick_po_dialog(frm) {
    if (!frm.doc.supplier) {
        frappe.msgprint("Pilih Supplier terlebih dahulu sebelum memilih Purchase Order.");
        return;
    }

    frappe.prompt([
        {
            fieldname: "po",
            label: "Purchase Order",
            fieldtype: "Link",
            options: "Purchase Order",
            reqd: 1,
            get_query: () => ({
                filters: {
                    supplier: frm.doc.supplier,
                    status: ["in", ["To Receive and Bill", "To Receive"]]
                }
            })
        }
    ], (values) => {
        frm._selected_po = values.po;
        frm.dashboard.clear_headline();
        frm.dashboard.set_headline(`<span>PO dipilih: <b>${frm._selected_po}</b></span>`);

        // Empty items table to prevent default auto-population
        frm.clear_table("items");
        frm.refresh_field("items");

        // Fetch PO items via parent DocType API
        frappe.call({
            method: 'frappe.client.get',
            args: { doctype: 'Purchase Order', name: frm._selected_po },
            callback: function (r) {
                console.log('Full PO Response:', r);
                const po = r && r.message ? r.message : {};
                const records = Array.isArray(po.items) ? po.items : [];

                console.log('PO Items Array:', records);

                frm._allowed_items = records.map(d => d.item_code);
                frm._po_item_map = {};
                frm._po_item_data = {}; // Cache full PO item data
                records.forEach(d => {
                    frm._po_item_map[d.item_code] = d.name;
                    frm._po_item_data[d.item_code] = d;

                    console.log(`PO Item ${d.item_code}:`, {
                        name: d.name,
                        rate: d.rate,
                        price_list_rate: d.price_list_rate,
                        base_rate: d.base_rate,
                        base_price_list_rate: d.base_price_list_rate,
                        qty: d.qty,
                        uom: d.uom,
                        warehouse: d.warehouse,
                        item_name: d.item_name,
                        description: d.description,
                        full_data: d
                    });
                });

                // Attach filter to items child grid to only show items from selected PO
                if (frm.fields_dict && frm.fields_dict.items && frm.fields_dict.items.grid) {
                    frm.fields_dict.items.grid.get_field('item_code').get_query = function (doc, cdt, cdn) {
                        return {
                            filters: [["Item", "name", "in", frm._allowed_items || []]]
                        };
                    };
                }

                // Set default warehouse from PO if specified
                if (po.set_warehouse) {
                    frappe.model.set_value(frm.doctype, frm.doc.name, 'set_warehouse', po.set_warehouse);
                    frappe.show_alert({
                        message: `PO ${frm._selected_po} terpilih. Default warehouse: ${po.set_warehouse}. Tambahkan item manual dari PO tersebut.`,
                        indicator: "blue"
                    });
                } else {
                    frappe.show_alert({
                        message: `PO ${frm._selected_po} terpilih. Tambahkan item manual dari PO tersebut.`,
                        indicator: "blue"
                    });
                }
            }
        });
    }, "Pilih Purchase Order", "Pilih");
}

function add_custom_po_button(frm) {
    // Remove standard button to prevent default ERPNext auto-population behavior
    if (frm.page && frm.page.remove_inner_button) {
        frm.page.remove_inner_button(__('Purchase Order'), __('Get Items From'));
    }
    frm.remove_custom_button("Purchase Order", "Get Items From");

    // Add custom pick button directly in the main toolbar
    frm.add_custom_button("Pilih Purchase Order", () => show_pick_po_dialog(frm));

    // Also add to Actions menu for visibility if group exists
    try {
        frm.add_custom_button("Pilih Purchase Order", () => show_pick_po_dialog(frm), "Actions");
    } catch (e) { /* ignore */ }
}

frappe.ui.form.on("Purchase Receipt", {
    onload(frm) {
        add_custom_po_button(frm);
        setup_rate_protection(frm);
    },
    refresh(frm) {
        add_custom_po_button(frm);
        setup_rate_protection(frm);
    }
});

// Setup rate protection monitor
function setup_rate_protection(frm) {
    if (!frm._rate_protection_active) {
        frm._rate_protection_active = true;

        if (frm._rate_monitor_interval) {
            clearInterval(frm._rate_monitor_interval);
        }

        frm._rate_monitor_interval = setInterval(() => {
            if (!frm.doc.items) return;

            frm.doc.items.forEach((item) => {
                if (item._po_rate_locked && item._po_rate !== undefined) {
                    let needs_update = false;

                    if (Math.abs(item.rate - item._po_rate) > 0.01) {
                        console.log(`[Rate Protection] Item ${item.item_code}: Restoring rate ${item._po_rate} (was ${item.rate})`);
                        item.rate = item._po_rate;
                        needs_update = true;
                    }

                    if (item._po_price_list_rate !== undefined && Math.abs(item.price_list_rate - item._po_price_list_rate) > 0.01) {
                        console.log(`[Rate Protection] Item ${item.item_code}: Restoring price_list_rate ${item._po_price_list_rate} (was ${item.price_list_rate})`);
                        item.price_list_rate = item._po_price_list_rate;
                        needs_update = true;
                    }

                    if (needs_update) {
                        frm.refresh_field('items');
                    }
                }
            });
        }, 500);

        $(frm.wrapper).on('unload', () => {
            if (frm._rate_monitor_interval) {
                clearInterval(frm._rate_monitor_interval);
            }
        });
    }
}

frappe.ui.form.on("Purchase Receipt Item", {
    item_code(frm, cdt, cdn) {
        if (!frm._selected_po) {
            frappe.msgprint("Pilih Purchase Order terlebih dahulu.");
            frappe.model.set_value(cdt, cdn, "item_code", "");
            return;
        }

        const row = locals[cdt][cdn];
        if (!row.item_code) return;

        // Set flags to indicate data comes from PO (protect from automatic override)
        row._is_from_po = true;
        row._po_rate_locked = true;

        if (frm._po_item_map && frm._po_item_map[row.item_code]) {
            frappe.model.set_value(cdt, cdn, 'purchase_order', frm._selected_po);
            frappe.model.set_value(cdt, cdn, 'purchase_order_item', frm._po_item_map[row.item_code]);

            const po_item = frm._po_item_data && frm._po_item_data[row.item_code];
            console.log('Looking for item:', row.item_code);
            console.log('PO Item Data found:', po_item);

            if (po_item) {
                const rate_to_set = po_item.rate || 0;
                const price_list_rate_to_set = (po_item.price_list_rate && po_item.price_list_rate > 0) ? po_item.price_list_rate : po_item.rate || 0;

                row._po_rate = rate_to_set;
                row._po_price_list_rate = price_list_rate_to_set;

                frappe.model.set_value(cdt, cdn, 'rate', rate_to_set);

                setTimeout(() => {
                    frappe.model.set_value(cdt, cdn, 'price_list_rate', price_list_rate_to_set);

                    setTimeout(() => {
                        frappe.model.set_value(cdt, cdn, 'discount_percentage', po_item.discount_percentage || 0);
                        frappe.model.set_value(cdt, cdn, 'discount_amount', po_item.discount_amount || 0);
                        frappe.model.set_value(cdt, cdn, 'uom', po_item.uom || '');
                        frappe.model.set_value(cdt, cdn, 'conversion_factor', po_item.conversion_factor || 1);
                        const warehouse_to_set = po_item.warehouse || frm.doc.set_warehouse || '';
                        frappe.model.set_value(cdt, cdn, 'warehouse', warehouse_to_set);
                        frappe.model.set_value(cdt, cdn, 'item_name', po_item.item_name || '');
                        frappe.model.set_value(cdt, cdn, 'description', po_item.description || '');

                        if (po_item.amount) frappe.model.set_value(cdt, cdn, 'amount', po_item.amount);
                        if (po_item.base_amount) frappe.model.set_value(cdt, cdn, 'base_amount', po_item.base_amount);
                        if (po_item.net_rate) frappe.model.set_value(cdt, cdn, 'net_rate', po_item.net_rate);
                        if (po_item.base_net_rate) frappe.model.set_value(cdt, cdn, 'base_net_rate', po_item.base_net_rate);
                        if (po_item.base_rate) frappe.model.set_value(cdt, cdn, 'base_rate', po_item.base_rate);
                        
                        const base_price_list_rate_to_set = (po_item.base_price_list_rate && po_item.base_price_list_rate > 0) ? po_item.base_price_list_rate : po_item.base_rate;
                        if (base_price_list_rate_to_set) {
                            frappe.model.set_value(cdt, cdn, 'base_price_list_rate', base_price_list_rate_to_set);
                        }

                        // Re-verify rate
                        setTimeout(() => {
                            const final_row = locals[cdt][cdn];
                            if (final_row._po_rate && final_row.rate != final_row._po_rate) {
                                frappe.model.set_value(cdt, cdn, 'rate', final_row._po_rate);
                            }
                            if (final_row._po_price_list_rate && final_row.price_list_rate != final_row._po_price_list_rate) {
                                frappe.model.set_value(cdt, cdn, 'price_list_rate', final_row._po_price_list_rate);
                            }

                            // Lock GUI inputs to prevent manual edits
                            const grid_row = frm.fields_dict.items.grid.grid_rows_by_docname[cdn];
                            if (grid_row) {
                                const rate_field = grid_row.get_field('rate');
                                const price_list_rate_field = grid_row.get_field('price_list_rate');
                                if (rate_field && rate_field.df) {
                                    rate_field.df.read_only = 1;
                                    rate_field.refresh();
                                }
                                if (price_list_rate_field && price_list_rate_field.df) {
                                    price_list_rate_field.df.read_only = 1;
                                    price_list_rate_field.refresh();
                                }
                            }
                            frm.refresh_field('items');
                        }, 200);
                    }, 100);
                }, 50);

                setTimeout(() => {
                    const warehouse_info = warehouse_to_set ? `, Warehouse: ${warehouse_to_set}` : '';
                    frappe.show_alert({
                        message: `Harga untuk ${row.item_code} telah diambil dari PO ${frm._selected_po} (Rate: ${rate_to_set})${warehouse_info}. Silakan input qty secara manual.`,
                        indicator: "green"
                    });
                }, 300);
            } else {
                frappe.msgprint(`Data item ${row.item_code} tidak ditemukan di cache PO.`);
            }
        } else {
            frappe.msgprint(`Item ${row.item_code} tidak ditemukan di PO ${frm._selected_po}.`);
            frappe.model.set_value(cdt, cdn, 'item_code', '');
        }
    },

    rate(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        if (row._po_rate_locked && row._po_rate !== undefined) {
            if (Math.abs(row.rate - row._po_rate) > 0.01) {
                frappe.show_alert({
                    message: `Rate dikunci dari PO. Rate harus sama dengan PO: ${row._po_rate}`,
                    indicator: 'orange'
                });
                frappe.model.set_value(cdt, cdn, 'rate', row._po_rate);
            }
        }
    },

    price_list_rate(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        if (row._po_rate_locked && row._po_price_list_rate !== undefined) {
            if (Math.abs(row.price_list_rate - row._po_price_list_rate) > 0.01) {
                frappe.model.set_value(cdt, cdn, 'price_list_rate', row._po_price_list_rate);
            }
        }
    },

    items_add(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        if (row) {
            row._is_from_po = false;
            row._po_rate_locked = false;
        }
    }
});
