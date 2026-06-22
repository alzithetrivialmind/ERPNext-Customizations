// ============================================================================
// Purchase Order Client Script - ERPNext v15
// PT. Palma Progress Shipyard
// ============================================================================
// 
// FEATURES:
// 1. Filter items berdasarkan PO Type
// 2. Auto-fill defaults (currency, warehouse, terms)
// 3. Auto-fill supplier attention dari primary contact
// 4. Validasi item sesuai PO Type
// 5. Last Purchase Rate tooltip (hover di item code)
// 6. Auto-clear description field
//
// PO TYPES:
// - Service Order  : Hanya item SV - Services (non-stock)
// - PO Steel LN    : Semua item kecuali SV - Services
// - PO Local       : Semua item kecuali SV - Services  
// - PO LN          : Semua item kecuali SV - Services
//
// ============================================================================

(function () {
    'use strict';

    // ========================================================================
    // CONFIGURATION
    // ========================================================================

    const CONFIG = {
        DEBUG: false, // Set true untuk enable logging

        // Item Groups
        SERVICE_GROUP: 'SV - Services',

        // Default warehouse
        DEFAULT_WAREHOUSE: 'Stores - PPS',

        // Default terms
        DEFAULT_TERMS: 'Place Delivery Our Yard PT. Palma Progress Shipyard Jl. Palma Kav. 1 Sagulung – Batam<br><br>Note: Please confirmed back to us with sign and chop',

        // PO Type defaults
        PO_DEFAULTS: {
            'PO Local': { currency: 'IDR' },
            'PO LN': { currency: '' },
            'PO Steel LN': { currency: '' },
            'Service Order': { currency: '' }
        },

        // Timing (ms)
        DESCRIPTION_CLEAR_DELAY: 1500,
        TOOLTIP_ATTACH_DELAY: 800,
        TOOLTIP_HIDE_DELAY: 300
    };

    // ========================================================================
    // UTILITY FUNCTIONS
    // ========================================================================

    function log(...args) {
        if (CONFIG.DEBUG) {
            console.log('[PO Script]', ...args);
        }
    }

    // ========================================================================
    // MAIN EVENT HANDLERS
    // ========================================================================

    frappe.ui.form.on('Purchase Order', {

        onload: function (frm) {
            log('onload triggered');

            if (frm.doc.__islocal) {
                setDefaults(frm);
            }

            applyItemFilter(frm);
        },

        refresh: function (frm) {
            log('refresh triggered, PO Type:', frm.doc.custom_po_type);

            if (frm.doc.__islocal) {
                setDefaults(frm);
            }

            applyItemFilter(frm);

            // Refresh tooltips untuk saved/draft PO
            setTimeout(() => refreshAllTooltips(frm), 1000);
        },

        custom_po_type: function (frm) {
            log('PO Type changed to:', frm.doc.custom_po_type);

            setDefaults(frm);
            applyItemFilter(frm);
        },

        supplier: function (frm) {
            if (!frm.doc.supplier) return;

            // Auto-populate supplier attention
            fetchSupplierAttention(frm);

            // Refresh tooltips untuk existing items
            setTimeout(() => refreshAllTooltips(frm), 500);
        },

        before_submit: function (frm) {
            if (!frm.doc.custom_po_type) {
                frappe.msgprint({
                    title: __('Validasi Gagal'),
                    message: __('PO Type harus dipilih sebelum submit.'),
                    indicator: 'red'
                });
                frappe.validated = false;
            }
        }
    });

    // ========================================================================
    // CHILD TABLE EVENT HANDLERS
    // ========================================================================

    frappe.ui.form.on('Purchase Order Item', {

        item_code: function (frm, cdt, cdn) {
            const row = locals[cdt][cdn];
            if (!row.item_code) return;

            log('item_code selected:', row.item_code);

            // Clear description after ERPNext populates it
            clearDescriptionDelayed(cdt, cdn, frm);

            // Fetch last purchase rate untuk tooltip
            if (frm.doc.supplier) {
                fetchLastPurchaseRate(frm, row.item_code, cdn);
            }

            // Validasi item
            if (frm.doc.custom_po_type) {
                validateItem(frm, row.item_code, frm.doc.custom_po_type, cdn);
            }
        }
    });

    // ========================================================================
    // ITEM FILTERING
    // ========================================================================

    /**
     * Apply filter ke dropdown item berdasarkan PO Type
     */
    function applyItemFilter(frm) {
        const poType = frm.doc.custom_po_type;

        if (!poType) {
            log('No PO Type selected, no filter applied');
            return;
        }

        log('Applying filter for:', poType);

        if (poType === 'Service Order') {
            // Service Order: hanya SV - Services (non-stock)
            setItemFilterInclude(frm, [CONFIG.SERVICE_GROUP], true);
        } else {
            // PO Steel LN / PO Local / PO LN: exclude SV - Services
            loadItemGroupDescendants(CONFIG.SERVICE_GROUP, (groups) => {
                setItemFilterExclude(frm, groups);
            });
        }
    }

    /**
     * Set filter untuk INCLUDE item groups tertentu
     */
    function setItemFilterInclude(frm, groups, nonStockOnly = false) {
        frm.fields_dict.items.grid.get_field('item_code').get_query = function () {
            const filters = {
                'disabled': 0,
                'item_group': ['in', groups]
            };

            if (nonStockOnly) {
                filters['is_stock_item'] = 0;
            }

            return { filters };
        };

        log('Filter set: INCLUDE', groups.length, 'groups');
    }

    /**
     * Set filter untuk EXCLUDE item groups tertentu
     */
    function setItemFilterExclude(frm, groups) {
        frm.fields_dict.items.grid.get_field('item_code').get_query = function () {
            return {
                filters: {
                    'disabled': 0,
                    'item_group': ['not in', groups]
                }
            };
        };

        log('Filter set: EXCLUDE', groups.length, 'groups');
    }

    /**
     * Load semua descendants dari item group (menggunakan Nested Set)
     */
    function loadItemGroupDescendants(parentGroup, callback) {
        frappe.call({
            method: 'frappe.client.get',
            args: {
                doctype: 'Item Group',
                name: parentGroup
            },
            callback: function (r) {
                if (!r.message) {
                    callback([parentGroup]);
                    return;
                }

                const { lft, rgt } = r.message;

                frappe.call({
                    method: 'frappe.client.get_list',
                    args: {
                        doctype: 'Item Group',
                        filters: [
                            ['lft', '>=', lft],
                            ['rgt', '<=', rgt]
                        ],
                        fields: ['name'],
                        limit_page_length: 999
                    },
                    callback: function (res) {
                        const groups = res.message
                            ? res.message.map(g => g.name)
                            : [parentGroup];

                        log('Loaded', groups.length, 'descendants for', parentGroup);
                        callback(groups);
                    }
                });
            }
        });
    }

    // ========================================================================
    // ITEM VALIDATION
    // ========================================================================

    /**
     * Validasi item apakah sesuai dengan PO Type
     */
    function validateItem(frm, itemCode, poType, cdn) {
        frappe.call({
            method: 'frappe.client.get',
            args: {
                doctype: 'Item',
                name: itemCode
            },
            callback: function (r) {
                if (!r.message) return;

                const itemGroup = r.message.item_group;
                const isServiceItem = (itemGroup === CONFIG.SERVICE_GROUP);

                let isValid = true;
                let errorMsg = '';

                if (poType === 'Service Order') {
                    // Service Order: harus SV - Services
                    if (!isServiceItem) {
                        isValid = false;
                        errorMsg = `Item "${itemCode}" bukan kategori ${CONFIG.SERVICE_GROUP}. Service Order hanya untuk item ${CONFIG.SERVICE_GROUP}.`;
                    }
                } else {
                    // PO Steel LN / PO Local / PO LN: tidak boleh SV - Services
                    if (isServiceItem) {
                        isValid = false;
                        errorMsg = `Item "${itemCode}" adalah kategori ${CONFIG.SERVICE_GROUP}. Item ini hanya diperbolehkan untuk Service Order.`;
                    }
                }

                if (!isValid) {
                    log('❌ Invalid item:', itemCode);

                    frappe.msgprint({
                        title: __('Item Tidak Valid'),
                        message: __(errorMsg),
                        indicator: 'red'
                    });

                    clearItemRow(cdn);
                } else {
                    log('✅ Valid item:', itemCode);
                }
            }
        });
    }

    /**
     * Clear semua field di item row
     */
    function clearItemRow(cdn) {
        const fields = ['item_code', 'item_name', 'description', 'qty', 'rate'];

        fields.forEach(field => {
            const value = (field === 'qty' || field === 'rate') ? 0 : '';
            frappe.model.set_value('Purchase Order Item', cdn, field, value);
        });
    }

    // ========================================================================
    // DEFAULTS & AUTO-FILL
    // ========================================================================

    /**
     * Set default values berdasarkan PO Type
     */
    function setDefaults(frm) {
        const poType = frm.doc.custom_po_type;
        if (!poType) return;

        const defaults = CONFIG.PO_DEFAULTS[poType];
        if (!defaults) return;

        // Set currency
        if (defaults.currency !== undefined) {
            frm.set_value('currency', defaults.currency);
        }

        // Set warehouse
        frm.set_value('set_warehouse', CONFIG.DEFAULT_WAREHOUSE);

        // Set terms
        frm.set_value('terms', CONFIG.DEFAULT_TERMS);

        log('Defaults set for:', poType);
    }

    /**
     * Fetch dan set supplier attention dari primary contact
     */
    function fetchSupplierAttention(frm) {
        frappe.call({
            method: 'frappe.client.get',
            args: {
                doctype: 'Supplier',
                name: frm.doc.supplier
            },
            callback: function (r) {
                if (!r.message?.supplier_primary_contact) return;

                frappe.call({
                    method: 'frappe.client.get',
                    args: {
                        doctype: 'Contact',
                        name: r.message.supplier_primary_contact
                    },
                    callback: function (res) {
                        if (!res.message) return;

                        const fullName = [
                            res.message.first_name,
                            res.message.last_name || ''
                        ].join(' ').trim();

                        frm.set_value('custom_supplier_attention', fullName);
                        log('Supplier attention set:', fullName);
                    }
                });
            }
        });
    }

    /**
     * Clear description field setelah delay
     */
    function clearDescriptionDelayed(cdt, cdn, frm) {
        setTimeout(() => {
            const row = locals[cdt][cdn];
            if (row?.item_code) {
                frappe.model.set_value(cdt, cdn, 'description', '');
                frm.refresh_field('items');
                log('Description cleared for:', row.item_code);
            }
        }, CONFIG.DESCRIPTION_CLEAR_DELAY);
    }

    // ========================================================================
    // LAST PURCHASE RATE TOOLTIP
    // ========================================================================

    let activePopover = null;
    let hideTimeout = null;

    /**
     * Fetch last purchase rate dan tampilkan tooltip
     */
    function fetchLastPurchaseRate(frm, itemCode, cdn) {
        log('Fetching last purchase for:', itemCode);

        frappe.call({
            method: 'get_last_purchase_rate',
            args: {
                supplier: frm.doc.supplier,
                item_code: itemCode
            },
            callback: function (r) {
                const tooltipData = buildTooltipData(r.message, frm.doc.currency);
                attachTooltip(cdn, itemCode, tooltipData);
            },
            error: function (err) {
                log('Error fetching last purchase:', err);
            }
        });
    }

    /**
     * Build tooltip data dari response
     */
    function buildTooltipData(purchases, currency) {
        if (!purchases || purchases.length === 0) {
            return {
                rate: 'N/A',
                poNumber: '',
                date: '',
                supplier: '',
                isFirstPurchase: true
            };
        }

        const lastPurchase = purchases[0];
        const formattedRate = format_currency(lastPurchase.rate, currency || 'IDR');
        const formattedDate = frappe.datetime.str_to_user(lastPurchase.transaction_date);

        return {
            rate: formattedRate,
            poNumber: lastPurchase.name || '',
            date: formattedDate,
            supplier: lastPurchase.supplier || '',
            isFirstPurchase: false
        };
    }

    /**
     * Attach tooltip ke item code cell
     */
    function attachTooltip(cdn, itemCode, tooltipData) {
        setTimeout(() => {
            const $row = $(`.grid-row[data-name="${cdn}"]`);
            if ($row.length === 0) {
                log('Row not found for tooltip');
                return;
            }

            const $itemCell = $row.find('[data-fieldname="item_code"]');
            if ($itemCell.length === 0) {
                // Retry jika cell belum ready
                setTimeout(() => attachTooltip(cdn, itemCode, tooltipData), 1000);
                return;
            }

            // Find target element
            let $target = $itemCell.find('.static-area a.indicator');
            if ($target.length === 0) $target = $itemCell.find('.static-area');
            if ($target.length === 0) $target = $itemCell.find('a').not('.btn-clear').first();

            if ($target.length === 0) {
                log('No target found for tooltip');
                return;
            }

            // Remove existing handlers
            $target.off('mouseenter.lastpurchase mouseleave.lastpurchase');

            // Attach hover handlers
            $target.on('mouseenter.lastpurchase', function () {
                if (hideTimeout) {
                    clearTimeout(hideTimeout);
                    hideTimeout = null;
                }
                showPopover($(this), tooltipData);
            });

            $target.on('mouseleave.lastpurchase', function () {
                hideTimeout = setTimeout(() => {
                    hidePopover();
                    hideTimeout = null;
                }, CONFIG.TOOLTIP_HIDE_DELAY);
            });

            log('Tooltip attached for:', itemCode);

        }, CONFIG.TOOLTIP_ATTACH_DELAY);
    }

    /**
     * Show popover
     */
    function showPopover($target, data) {
        hidePopover();

        // Build content
        let rateText, detailText;

        if (data.isFirstPurchase) {
            rateText = '💰 Last Purchase: N/A';
            detailText = '📋 First time purchase from this supplier';
        } else {
            rateText = `💰 Last Purchase: ${data.rate}`;

            const details = [];
            if (data.poNumber) details.push(data.poNumber);
            if (data.date) details.push(data.date);
            if (data.supplier) details.push(`from ${data.supplier}`);

            detailText = details.length > 0 ? `📅 ${details.join(', ')}` : '';
        }

        // Create popover element
        const $popover = $('<div>')
            .attr('id', 'last-purchase-popover')
            .css({
                position: 'fixed',
                background: '#2c3e50',
                color: '#ecf0f1',
                padding: '8px 12px',
                borderRadius: '6px',
                fontSize: '11px',
                boxShadow: '0 4px 12px rgba(0,0,0,0.25)',
                zIndex: '10000',
                pointerEvents: 'none',
                whiteSpace: 'nowrap',
                fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif',
                lineHeight: '1.5',
                border: '1px solid rgba(255,255,255,0.1)'
            })
            .html(`
                <div style="font-weight: 600; color: #3498db; margin-bottom: 4px; font-size: 12px;">${rateText}</div>
                ${detailText ? `<div style="font-size: 10px; color: #bdc3c7; opacity: 0.9;">${detailText}</div>` : ''}
            `);

        $('body').append($popover);
        positionPopover($popover, $target);
        activePopover = $popover;
    }

    /**
     * Hide popover
     */
    function hidePopover() {
        if (activePopover) {
            activePopover.remove();
            activePopover = null;
        }
    }

    /**
     * Position popover relative to target
     */
    function positionPopover($popover, $target) {
        const targetRect = $target[0].getBoundingClientRect();
        const popoverWidth = $popover.outerWidth();
        const popoverHeight = $popover.outerHeight();
        const viewportWidth = window.innerWidth;

        // Position above target, left-aligned
        let left = targetRect.left - 10;
        let top = targetRect.top - popoverHeight - 10;

        // Keep within viewport
        if (left < 10) left = 10;
        if (left + popoverWidth > viewportWidth - 10) {
            left = targetRect.right - popoverWidth;
            if (left < 10) left = 10;
        }

        // Show below if no space above
        if (top < 10) {
            top = targetRect.bottom + 8;
        }

        $popover.css({ left: left + 'px', top: top + 'px' });
    }

    /**
     * Refresh tooltips untuk semua items (untuk saved/draft PO)
     */
    function refreshAllTooltips(frm) {
        if (!frm.doc.supplier || !frm.doc.items?.length) {
            return;
        }

        log('Refreshing tooltips for', frm.doc.items.length, 'items');

        frm.doc.items.forEach(item => {
            if (item.item_code) {
                fetchLastPurchaseRate(frm, item.item_code, item.name);
            }
        });
    }

    // ========================================================================
    // INITIALIZATION
    // ========================================================================

    log('Script loaded successfully!');

})();
