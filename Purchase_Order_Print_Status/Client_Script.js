frappe.ui.form.on('Purchase Order', {
    refresh(frm) {
        // Add "Mark as Printed" button in the toolbar
        if (!frm.doc.is_printed && frm.doc.docstatus == 1) {
            frm.add_custom_button(__('Tandai Sudah Dicetak'), function () {
                frm.set_value('is_printed', 1);
                frm.save();
                frappe.show_alert({
                    message: __('Purchase Order telah ditandai sebagai sudah dicetak'),
                    indicator: 'green'
                }, 5);
            });
        }
    },

    print_format: function (frm) {
        // Mark as printed when print action is triggered
        frm.set_value('is_printed', 1);
        frm.save();

        // Show confirmation alert
        frappe.show_alert({
            message: __('Purchase Order telah ditandai sebagai sudah dicetak'),
            indicator: 'green'
            }, 5);
    }
});
