app_name = "advanced_discounting"
app_title = "Advanced Discounting"
app_publisher = "Palma Progress Shipyard"
app_description = "PO→PR discount allocation and PI/PR discount management"
app_email = "alzi@palmashipyard.com"
app_license = "MIT"
required_apps = ["frappe", "erpnext"]

# --------------------------------------------------------------------------
# Client-side scripts loaded on every Desk page
# --------------------------------------------------------------------------
app_include_js = [
    "/assets/advanced_discounting/js/purchase_invoice.js",
    "/assets/advanced_discounting/js/purchase_receipt.js",
]

# --------------------------------------------------------------------------
# Document Events
# --------------------------------------------------------------------------
doc_events = {
    "Purchase Receipt": {
        "validate": (
            "advanced_discounting.discount_allocation"
            ".purchase_receipt_discount.validate"
        ),
        "on_cancel": (
            "advanced_discounting.discount_allocation"
            ".purchase_receipt_discount.on_cancel"
        ),
    },
    "Purchase Invoice": {
        "before_validate": (
            "advanced_discounting.purchase_discounting"
            ".purchase_invoice_discount.before_validate"
        ),
    },
}

# --------------------------------------------------------------------------
# Fixtures — Custom Fields exported with `bench export-fixtures`
# --------------------------------------------------------------------------
fixtures = [
    {
        "dt": "Custom Field",
        "filters": [
            [
                "name",
                "in",
                [
                    # ── Module 1: PO → PR Proportional Discount ──
                    "Purchase Order Item-custom_disc_eligible",
                    "Purchase Receipt-custom_disc_is_historical",
                    "Purchase Receipt-custom_disc_allocation_log",
                    "Purchase Receipt Item-custom_disc_allocated_discount",
                    # ── Module 2: PI discount fields (already exist) ──
                    "Purchase Invoice Item-custom_palma_base_rate",
                    "Purchase Invoice Item-custom_palma_discount_type",
                    "Purchase Invoice Item-custom_palma_discount_amount",
                    "Purchase Invoice-custom_palma_global_disc_type",
                    "Purchase Invoice-custom_palma_global_disc_value",
                    "Purchase Invoice-custom_apply_global_discount",
                    # ── Module 2: PR discount sync fields ──
                    "Purchase Receipt Item-custom_palma_base_rate",
                    "Purchase Receipt Item-custom_palma_discount_type",
                    "Purchase Receipt Item-custom_palma_discount_amount",
                    "Purchase Receipt-custom_palma_global_disc_type",
                    "Purchase Receipt-custom_palma_global_disc_value",
                    "Purchase Receipt-custom_apply_global_discount",
                ],
            ]
        ],
    }
]
