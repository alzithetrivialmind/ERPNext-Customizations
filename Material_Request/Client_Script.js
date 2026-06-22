// Material Request - Grid Only Setup
// Global: set grid items to the following order and columns for all purposes:
// Item Code | Qty | UoM | Item Name | Item Group | Actual Qty | Project | Description

frappe.ui.form.on('Material Request', {
    onload: function (frm) {
        setupHeaderFields(frm);
        setupDynamicBehavior(frm);
    },
    refresh: function (frm) {
        setupHeaderFields(frm);
        setupDynamicBehavior(frm);
    },
    items_add: function (frm, cdt, cdn) {
        applyHeaderDefaultsToItem(frm, cdt, cdn);
    }
});

function ensureItemsGridConfigured(frm, delayMs) {
    // Intentionally left empty to respect manual grid setup
}

function setupItemsGridColumns(frm) {
    if (!frm.fields_dict.items || !frm.fields_dict.items.grid) return;
    var grid = frm.fields_dict.items.grid;
    // List of columns to make visible (in order)
    var visible = [
        'item_code',
        'qty',
        'uom',
        'item_name',
        'item_group',
        'actual_qty',
        'project',
        'description'
    ];

    var widths = {
        'item_code': 1.8,
        'qty': 0.8,
        'uom': 0.8,
        'item_name': 2,
        'item_group': 1.4,
        'actual_qty': 1,
        'project': 1.6,
        'description': 3
    };

    try {
        if (!grid.docfields || grid.docfields.length === 0) return;
        // Show/hide columns and set width
        grid.docfields.forEach(function (df) {
            if (visible.indexOf(df.fieldname) !== -1) {
                df.hidden = 0;
                df.in_list_view = 1;
                if (widths[df.fieldname]) df.columns = widths[df.fieldname];
            } else {
                df.hidden = 1;
                df.in_list_view = 0;
            }
        });
        if (grid.docfields_by_name) {
            Object.keys(grid.docfields_by_name).forEach(function (fn) {
                var df = grid.docfields_by_name[fn];
                if (visible.indexOf(fn) !== -1) {
                    df.hidden = 0;
                    df.in_list_view = 1;
                    if (widths[fn]) df.columns = widths[fn];
                } else {
                    df.hidden = 1;
                    df.in_list_view = 0;
                }
            });
        }
        grid.refresh();
        frm.refresh_field('items');
    } catch (e) {
        console.error('Grid setup error', e);
    }
}

function setupHeaderFields(frm) {
    // Project
    if (frm.fields_dict.project) {
        frm.set_df_property('project', 'hidden', 0);
        // Query: exclude completed/cancelled projects
        frm.set_query('project', function () {
            return {
                filters: { 'status': ['not in', ['Completed', 'Cancelled']] }
            };
        });
    }

    // Subcontractor (custom_subcontractor)
    if (frm.fields_dict.custom_subcontractor) {
        frm.set_df_property('custom_subcontractor', 'hidden', 0);
        frm.set_query('custom_subcontractor', function () {
            return {
                filters: { 'supplier_group': ['in', ['Subcontractor', 'Palma Internal']] }
            };
        });
    }

    // Item Group header (support multiple potential fieldnames)
    var itemGroupField = getItemGroupHeaderFieldname(frm);
    if (itemGroupField) {
        frm.set_df_property(itemGroupField, 'hidden', 0);
        // Display group (not leaf) as category
        frm.set_query(itemGroupField, function () {
            return {
                filters: { 'is_group': 1 }
            };
        });
    }
}

function getItemGroupHeaderFieldname(frm) {
    if (frm.fields_dict.item_group && frm.fields_dict.item_group.df.options === 'Item Group') {
        return 'item_group';
    }
    if (frm.fields_dict.custom_categories_level_1 && frm.fields_dict.custom_categories_level_1.df.options === 'Item Group') {
        return 'custom_categories_level_1';
    }
    if (frm.fields_dict.custom_item_group && frm.fields_dict.custom_item_group.df.options === 'Item Group') {
        return 'custom_item_group';
    }
    return null;
}

// Script to setup grid columns in Material Request
frappe.ui.form.on('Material Request', {
    refresh: function (frm) {
        setupItemsGridColumns(frm);
    }
});

function setupItemsGridColumns(frm) {
    // Intentionally disabled to respect manual column order/visibility
}

function resolveFieldnames(frm) {
    var fieldnames = {
        categories: null,
        project: null,
        subcontractor: null
    };
    if (frm.fields_dict.custom_categories) fieldnames.categories = 'custom_categories';
    else if (frm.fields_dict.custom_categories_level_1) fieldnames.categories = 'custom_categories_level_1';
    else if (frm.fields_dict.item_group && frm.fields_dict.item_group.df.options === 'Item Group') fieldnames.categories = 'item_group';

    fieldnames.project = frm.fields_dict.custom_project ? 'custom_project' : (frm.fields_dict.project ? 'project' : null);
    fieldnames.subcontractor = frm.fields_dict.custom_subcontractor ? 'custom_subcontractor' : (frm.fields_dict.subcontractor ? 'subcontractor' : null);
    return fieldnames;
}

function setupDynamicBehavior(frm) {
    var f = resolveFieldnames(frm);
    setHeaderQueries(frm, f);
    setItemCodeQuery(frm, f);
    setRequiredByType(frm, f);
    setupProjectAutofill(frm, f);
}

function setHeaderQueries(frm, f) {
    if (f.project) {
        frm.set_query(f.project, function () {
            return {
                filters: { status: ['not in', ['Completed', 'Completed', 'Cancelled']] }
            };
        });
    }
    if (f.subcontractor) {
        frm.set_query(f.subcontractor, function () {
            return {
                filters: { supplier_group: ['in', ['Subcontractor', 'Palma Internal']] }
            };
        });
    }
    if (f.categories) {
        frm.set_query(f.categories, function () {
            return { filters: { is_group: 1 } };
        });
    }
}

function setItemCodeQuery(frm, f) {
    if (!frm.fields_dict.items) return;
    frm.set_query('item_code', 'items', function (doc, cdt, cdn) {
        var filters = { disabled: 0 };
        var cat = f.categories ? frm.doc[f.categories] : null;
        if (cat) {
            filters.item_group = cat;
        }
        return { filters: filters };
    });
}

function setRequiredByType(frm, f) {
    var isReq = ['Material Issue', 'Purchase'].indexOf(frm.doc.material_request_type) !== -1;
    if (f.subcontractor) frm.toggle_reqd(f.subcontractor, isReq);
    if (f.categories) frm.toggle_reqd(f.categories, isReq);
    if (f.project) frm.toggle_reqd(f.project, isReq);
}

function setupProjectAutofill(frm, f) {
    if (!f.project) return;
    // Apply on header change
    frm.script_manager.trigger(f.project);
    frm.fields_dict[f.project].df.onchange = function () {
        applyProjectToAllItems(frm, f);
    };
    // Initial sync
    applyProjectToAllItems(frm, f);
}

function applyProjectToAllItems(frm, f) {
    if (!f.project || !frm.doc.items) return;
    var headerProject = frm.doc[f.project];
    (frm.doc.items || []).forEach(function (row) {
        row.project = headerProject || row.project;
    });
    frm.refresh_field('items');
}

function applyHeaderDefaultsToItem(frm, cdt, cdn) {
    var f = resolveFieldnames(frm);
    var row = locals[cdt][cdn];
    if (f && f.project && frm.doc[f.project]) {
        row.project = frm.doc[f.project];
    }
    frm.refresh_field('items');
}
