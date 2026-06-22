frappe.ui.form.on('Item Creator', {
    refresh(frm) {
        // Filter group_level_1: only direct parents under All Item Groups
        frm.set_query('group_level_1', () => ({
            filters: {
                parent_item_group: 'All Item Groups',
                is_group: 1
            },
            page_len: 500
        }));
        frm.set_query('group_level_2', () => ({
            filters: { parent_item_group: frm.doc.group_level_1 },
            page_len: 500
        }));
        frm.set_query('group_level_3', () => ({
            filters: { parent_item_group: frm.doc.group_level_2 },
            page_len: 500
        }));

        update_preview(frm);
        frm.toggle_enable('group_level_2', !!frm.doc.group_level_1);
        frm.toggle_enable('group_level_3', !!frm.doc.group_level_2);

        // Change primary action to "Create Item" and disable standard Save
        frm.disable_save();
        set_primary_action(frm);
    }
    ,

    group_level_1(frm) {
        frm.set_value('group_level_2', null);
        frm.set_value('group_level_3', null);
        update_preview(frm);
        frm.toggle_enable('group_level_2', !!frm.doc.group_level_1);
        frm.toggle_enable('group_level_3', false);
    },

    group_level_2(frm) {
        frm.set_value('group_level_3', null);
        update_preview(frm);
        frm.toggle_enable('group_level_3', !!frm.doc.group_level_2);
    },

    group_level_3(frm) {
        update_preview(frm);
        fetch_last_code(frm);
    },

    variant_code(frm) {
        // Update preview when variant code changes
        update_preview(frm);
    }
});

function format_variant_code(raw_code) {
    const raw = raw_code || '';
    return raw.replace(/[^a-zA-Z0-9]/g, '').toUpperCase();
}

function update_preview(frm) {
    const l1 = frm.doc.group_level_1 || '';
    const l2 = frm.doc.group_level_2 || '';
    const l3 = frm.doc.group_level_3 || '';
    const variant_code = frm.doc.variant_code || '';

    const a = parse_l1(l1);
    const b = parse_l2(l2);
    const c = parse_l3(l3);

    let preview = '';

    // Build base code
    if (a && b && c) {
        const base = `${a}-${b}-${c}`;

        // Parse variant code
        let variant = '';
        if (variant_code) {
            // Remove non-alphanumeric and convert to uppercase
            const clean = variant_code.replace(/[^a-zA-Z0-9]/g, '').toUpperCase();

            // Extract digits and optional letter
            const digits = clean.replace(/[^0-9]/g, '');
            const letter = clean.replace(/[0-9]/g, '').charAt(0); // Take first letter only

            if (digits) {
                // Pad to 3 digits
                variant = digits.padStart(3, '0').substring(0, 3) + letter;
            }
        }

        preview = variant ? `${base}${variant}` : base;
    }

    frm.set_value('preview_code', preview);
}

function set_primary_action(frm) {
    frm.page.set_primary_action(__('Create Item'), () => {
        // Client-side validation
        if (!frm.doc.group_level_1 || !frm.doc.group_level_2 || !frm.doc.group_level_3) {
            frappe.msgprint(__('Lengkapi Group Level 1 → 2 → 3.'));
            return;
        }
        if (!frm.doc.stock_uom) {
            frappe.msgprint(__('Stock UoM wajib diisi.'));
            return;
        }

        // Validate and generate item code
        const item_code = frm.doc.preview_code;
        if (!item_code) {
            frappe.msgprint(__('Kode item tidak valid. Pastikan semua field terisi dengan benar.'));
            return;
        }

        // Set default values for new Item form
        frappe.route_options = {
            item_code: item_code,
            item_name: frm.doc.item_name || item_code,
            item_group: frm.doc.group_level_3, // Use Level 3 as Item Group
            stock_uom: frm.doc.stock_uom,
            description: frm.doc.description || '',
            is_stock_item: 1 // Always default to maintain stock
        };

        // Redirect to full Item form (not quick entry dialog)
        frappe.set_route('Form', 'Item', 'new-item-1');
    });
}

/**
 * Generic parser: extract code before first space
 * Format: "CODE - Description" -> "CODE"
 * Max 4 alphanumeric characters, any combination allowed
 */
function parse_code_generic(name) {
    if (!name) return '';

    // Split by first space to get the code part
    const code = name.split(' ')[0].trim();

    if (!code) return '';

    // Remove non-alphanumeric and convert to uppercase
    const clean_code = code.replace(/[^a-zA-Z0-9]/g, '').toUpperCase();

    // Validate: 1-4 characters
    if (clean_code.length >= 1 && clean_code.length <= 4) {
        return clean_code;
    }

    return '';
}

function parse_l1(name) {
    return parse_code_generic(name);
}

function parse_l2(name) {
    return parse_code_generic(name);
}

function parse_l3(name) {
    return parse_code_generic(name);
}

/**
 * Fetch the last used item code for the selected group hierarchy
 * Displays in the 'last_code' field to help users choose next variant
 */
function fetch_last_code(frm) {
    // Parse base code from selected groups
    const l1 = frm.doc.group_level_1 || '';
    const l2 = frm.doc.group_level_2 || '';
    const l3 = frm.doc.group_level_3 || '';

    const code_l1 = parse_l1(l1);
    const code_l2 = parse_l2(l2);
    const code_l3 = parse_l3(l3);

    // Clear last_code if any level is missing or invalid
    if (!code_l1 || !code_l2 || !code_l3) {
        frm.set_value('last_code', '');
        return;
    }

    // Build base code pattern
    const base_code = `${code_l1}-${code_l2}-${code_l3}`;

    // Query database for latest item with this base code
    frappe.call({
        method: 'frappe.client.get_list',
        args: {
            doctype: 'Item',
            filters: [
                ['item_code', 'like', `${base_code}%`]
            ],
            fields: ['item_code', 'item_name'],
            order_by: 'item_code desc',
            limit_page_length: 1
        },
        callback: (r) => {
            if (r.message && r.message.length > 0) {
                const last_item = r.message[0];
                // Display full item code
                frm.set_value('last_code', last_item.item_code);
            } else {
                // No previous items found for this category
                frm.set_value('last_code', 'No previous items');
            }
        },
        error: (r) => {
            // Handle error gracefully
            frm.set_value('last_code', '');
            console.error('Error fetching last code:', r);
        }
    });
}
