# Copyright (c) 2026, Palma Progress Shipyard and contributors
# For license information, please see license.txt

"""
Tests for Module 2 — Purchase Invoice Row & Global Discount

Covers:
  - Test Case 5: Row discount — Percentage
  - Test Case 6: Row discount — Amount (total for row)
  - Test Case 9: Server-side fallback (API/import)
"""

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import flt


class TestPurchaseInvoiceDiscount(FrappeTestCase):
    """Acceptance tests for Purchase Invoice discount calculations."""

    def setUp(self):
        """Create reusable test items if they don't exist."""
        for code in ["TEST-PI-DISC-001", "TEST-PI-DISC-002"]:
            if not frappe.db.exists("Item", code):
                item = frappe.get_doc({
                    "doctype": "Item",
                    "item_code": code,
                    "item_name": f"Test PI Discount Item {code}",
                    "item_group": "All Item Groups",
                    "stock_uom": "Nos",
                    "is_stock_item": 1,
                })
                item.insert(ignore_permissions=True)

    def _get_supplier(self):
        """Get or create a test supplier."""
        name = "_Test Supplier PI Discount"
        if not frappe.db.exists("Supplier", name):
            frappe.get_doc({
                "doctype": "Supplier",
                "supplier_name": name,
                "supplier_group": "All Supplier Groups",
            }).insert(ignore_permissions=True)
        return name

    # ──────────────────────────────────────────────────────────
    #  TEST CASE 5: Row discount — Percentage
    # ──────────────────────────────────────────────────────────

    def test_row_discount_percentage(self):
        """Test percentage row discount server-side calculation."""
        pi = frappe.get_doc({
            "doctype": "Purchase Invoice",
            "supplier": self._get_supplier(),
            "items": [
                {
                    "item_code": "TEST-PI-DISC-001",
                    "qty": 5,
                    # We only set the custom Palma fields to test the fallback calc
                    "custom_palma_base_rate": 100000,
                    "custom_palma_discount_type": "Percentage",
                    "custom_palma_discount_amount": 10,
                }
            ]
        })
        pi.insert(ignore_permissions=True)

        item = pi.items[0]
        self.assertEqual(flt(item.price_list_rate), 100000)
        self.assertEqual(flt(item.discount_percentage), 10)
        self.assertEqual(flt(item.discount_amount), 10000)  # 10% of 100k
        self.assertEqual(flt(item.rate), 90000)

    # ──────────────────────────────────────────────────────────
    #  TEST CASE 6: Row discount — Amount (total for row)
    # ──────────────────────────────────────────────────────────

    def test_row_discount_amount(self):
        """Test amount row discount server-side calculation (dval / qty)."""
        pi = frappe.get_doc({
            "doctype": "Purchase Invoice",
            "supplier": self._get_supplier(),
            "items": [
                {
                    "item_code": "TEST-PI-DISC-001",
                    "qty": 5,
                    "custom_palma_base_rate": 100000,
                    "custom_palma_discount_type": "Amount",
                    "custom_palma_discount_amount": 25000,  # total for the row
                }
            ]
        })
        pi.insert(ignore_permissions=True)

        item = pi.items[0]
        self.assertEqual(flt(item.price_list_rate), 100000)
        self.assertEqual(flt(item.discount_amount), 5000)  # 25000 / 5
        self.assertEqual(flt(item.discount_percentage), 5) # 5000 / 100000
        self.assertEqual(flt(item.rate), 95000)

    # ──────────────────────────────────────────────────────────
    #  TEST CASE 9: Server-side fallback
    # ──────────────────────────────────────────────────────────

    def test_server_side_fallback_from_price_list_rate(self):
        """Test that if custom_palma_base_rate is 0, it falls back to price_list_rate."""
        pi = frappe.get_doc({
            "doctype": "Purchase Invoice",
            "supplier": self._get_supplier(),
            "items": [
                {
                    "item_code": "TEST-PI-DISC-001",
                    "qty": 1,
                    "price_list_rate": 50000,
                    # custom_palma_base_rate is intentionally left 0
                    "custom_palma_discount_type": "Percentage",
                    "custom_palma_discount_amount": 20,
                }
            ]
        })
        pi.insert(ignore_permissions=True)

        item = pi.items[0]
        # It should have synced the base rate
        self.assertEqual(flt(item.custom_palma_base_rate), 50000)
        self.assertEqual(flt(item.discount_amount), 10000)
        self.assertEqual(flt(item.rate), 40000)
