// Client Script (Apply To: List) for Doctype: Item

// Effect: Clicking "Add Item" in Item List opens Item Creator instead
function ensure_black_btn_style() {
    if (document.getElementById('erp-black-btn-style')) return;
    const style = document.createElement('style');
    style.id = 'erp-black-btn-style';
    style.textContent = `
		.erp-btn-black { background: #000 !important; color: #fff !important; border-color: #000 !important; }
		.erp-btn-black:hover, .erp-btn-black:focus { background: #111 !important; border-color: #111 !important; color: #fff !important; }
	`;
    document.head.appendChild(style);
}

function override_item_list_primary_action(listview) {
    if (!listview || !listview.page) return;
    // Clear and set a new primary action after listview renders
    listview.page.clear_primary_action();

    // Primary: Add Item (via Item Creator)
    const addItemBtn = listview.page.set_primary_action(__('Add Item'), () => {
        frappe.new_doc('Item Creator');
    });

    // Style primary to black/white
    ensure_black_btn_style();
    if (addItemBtn && addItemBtn.$btn) {
        addItemBtn.$btn.addClass('erp-btn-black');
    }

    // Add Service button as secondary action (adjacent to Add Item)
    if (!listview._erp_item_actions_added) {
        const secondary = listview.page.set_secondary_action(__('Add Service'), () => {
            frappe.route_options = {
                item_group: 'SE - Services',
                is_stock_item: 0
            };
            frappe.set_route('Form', 'Item', 'new-item-1');
        });

        // Make secondary look like primary (black background, white text)
        ensure_black_btn_style();
        if (secondary && secondary.$btn) {
            secondary.$btn.addClass('erp-btn-black');
        }

        // Also add to Actions menu for visibility
        listview.page.add_actions_menu_item(__('Add Service'), () => {
            frappe.route_options = {
                item_group: 'SE - Services',
                is_stock_item: 0
            };
            frappe.set_route('Form', 'Item', 'new-item-1');
        });

        listview._erp_item_actions_added = true;
    }
}

frappe.listview_settings['Item'] = {
    onload(listview) {
        override_item_list_primary_action(listview);
        setTimeout(() => override_item_list_primary_action(listview), 0);
    },
    refresh(listview) {
        setTimeout(() => override_item_list_primary_action(listview), 0);
    }
};
