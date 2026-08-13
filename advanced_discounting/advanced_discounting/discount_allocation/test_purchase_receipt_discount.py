# Copyright (c) 2026, Palma Progress Shipyard and contributors
# For license information, please see license.txt

"""
Tests for Module 1 — PO → PR Proportional Discount Allocation

Covers:
  - Test Case 1:  PO 326,760,000 / discount 6,760,000 split across two PRs
  - Test Case 2:  Multi-PO-per-PR grouping
  - Test Case 3:  Cancel/Amend reversal
  - Test Case 4:  Non-eligible items skipped
  - Test Case 10: Data Import Tool bypass (historical guard)
  - Test Case 11: custom_disc_is_historical checkbox
"""

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import flt


class TestPurchaseReceiptDiscount(FrappeTestCase):
    """Acceptance tests for proportional discount allocation."""

    def setUp(self):
        """Create reusable test items if they don't exist."""
        for code in ["TEST-DISC-001", "TEST-DISC-002", "TEST-DISC-003"]:
            if not frappe.db.exists("Item", code):
                item = frappe.get_doc({
                    "doctype": "Item",
                    "item_code": code,
                    "item_name": f"Test Discount Item {code}",
                    "item_group": "All Item Groups",
                    "stock_uom": "Nos",
                    "is_stock_item": 1,
                })
                item.insert(ignore_permissions=True)

    # ──────────────────────────────────────────────────────────
    #  HELPERS
    # ──────────────────────────────────────────────────────────

    def _make_po(self, items, discount_percentage=0):
        """Create and submit a Purchase Order.

        Args:
            items: list of dicts with keys: item_code, qty, rate, eligible
            discount_percentage: applied via price_list_rate / discount_amount
        """
        po = frappe.get_doc({
            "doctype": "Purchase Order",
            "supplier": self._get_supplier(),
            "schedule_date": frappe.utils.today(),
            "items": [],
        })
        for i in items:
            row = po.append("items", {
                "item_code": i["item_code"],
                "qty": i["qty"],
                "rate": i["rate"],
                "price_list_rate": i["rate"],
                "schedule_date": frappe.utils.today(),
                "warehouse": self._get_warehouse(),
            })
            # Set discount if specified
            if discount_percentage:
                row.discount_percentage = discount_percentage
                row.discount_amount = flt(i["rate"] * discount_percentage / 100, 2)
                row.rate = flt(i["rate"] - row.discount_amount, 2)
            # Set eligibility flag
            row.custom_disc_eligible = 1 if i.get("eligible", True) else 0

        po.insert(ignore_permissions=True)
        po.submit()
        return po

    def _make_pr(self, po, items_qty, is_historical=False):
        """Create a Purchase Receipt linked to a PO.

        Args:
            po: Purchase Order doc
            items_qty: dict of {item_code: qty_to_receive}
            is_historical: set the historical entry guard
        """
        pr = frappe.get_doc({
            "doctype": "Purchase Receipt",
            "supplier": po.supplier,
            "custom_disc_is_historical": 1 if is_historical else 0,
            "items": [],
        })
        for po_item in po.items:
            qty = items_qty.get(po_item.item_code, 0)
            if qty <= 0:
                continue
            pr.append("items", {
                "item_code": po_item.item_code,
                "qty": qty,
                "rate": po_item.rate,
                "price_list_rate": po_item.price_list_rate,
                "warehouse": self._get_warehouse(),
                "purchase_order": po.name,
                "purchase_order_item": po_item.name,
            })

        pr.insert(ignore_permissions=True)
        return pr

    def _get_supplier(self):
        """Get or create a test supplier."""
        name = "_Test Supplier Discount"
        if not frappe.db.exists("Supplier", name):
            frappe.get_doc({
                "doctype": "Supplier",
                "supplier_name": name,
                "supplier_group": "All Supplier Groups",
            }).insert(ignore_permissions=True)
        return name

    def _get_warehouse(self):
        """Return a valid warehouse."""
        wh = frappe.db.get_value(
            "Warehouse",
            {"is_group": 0, "company": frappe.defaults.get_defaults().get("company")},
            "name",
        )
        return wh or "Stores - _TC"

    # ──────────────────────────────────────────────────────────
    #  TEST CASE 1: PO split across two PRs
    # ──────────────────────────────────────────────────────────

    def test_proportional_split_two_prs(self):
        """PO total ~326M with ~6.76M discount split across 2 PRs."""
        po = self._make_po(
            items=[
                {"item_code": "TEST-DISC-001", "qty": 100, "rate": 1000000, "eligible": True},
                {"item_code": "TEST-DISC-002", "qty": 100, "rate": 1267600, "eligible": True},
                {"item_code": "TEST-DISC-003", "qty": 100, "rate": 1000000, "eligible": True},
            ],
            discount_percentage=2.07,  # ~6.76M total discount
        )

        total_po_discount = sum(
            flt(poi.discount_amount) * flt(poi.qty)
            for poi in po.items
            if poi.custom_disc_eligible
        )
        self.assertGreater(total_po_discount, 0)

        # PR #1: receive 60% of each item
        pr1 = self._make_pr(po, {
            "TEST-DISC-001": 60,
            "TEST-DISC-002": 60,
            "TEST-DISC-003": 60,
        })
        pr1.submit()
        pr1.reload()

        pr1_total_allocated = sum(
            flt(item.custom_disc_allocated_discount)
            for item in pr1.items
        )
        self.assertGreater(pr1_total_allocated, 0)

        # PR #2: receive remaining 40% (closing receipt)
        pr2 = self._make_pr(po, {
            "TEST-DISC-001": 40,
            "TEST-DISC-002": 40,
            "TEST-DISC-003": 40,
        })
        pr2.submit()
        pr2.reload()

        pr2_total_allocated = sum(
            flt(item.custom_disc_allocated_discount)
            for item in pr2.items
        )
        self.assertGreater(pr2_total_allocated, 0)

        # Verify: sum matches PO discount exactly
        grand_total_allocated = pr1_total_allocated + pr2_total_allocated
        self.assertAlmostEqual(
            grand_total_allocated, total_po_discount, places=2,
            msg=f"Sum of allocations ({grand_total_allocated}) != PO discount ({total_po_discount})"
        )

        # Verify allocation log rows exist
        self.assertTrue(len(pr1.custom_disc_allocation_log) > 0)
        self.assertTrue(len(pr2.custom_disc_allocation_log) > 0)

        # Verify closing receipt has remainder method
        closing_methods = [
            log.allocation_method for log in pr2.custom_disc_allocation_log
        ]
        self.assertIn("remainder", closing_methods)

    # ──────────────────────────────────────────────────────────
    #  TEST CASE 2: Multi-PO per PR
    # ──────────────────────────────────────────────────────────

    def test_multi_po_per_pr(self):
        """Single PR with items from two different POs."""
        po_a = self._make_po(
            items=[{"item_code": "TEST-DISC-001", "qty": 10, "rate": 100000, "eligible": True}],
            discount_percentage=5.0,
        )
        po_b = self._make_po(
            items=[{"item_code": "TEST-DISC-002", "qty": 10, "rate": 200000, "eligible": True}],
            discount_percentage=3.0,
        )

        # Build PR manually with items from both POs
        pr = frappe.get_doc({
            "doctype": "Purchase Receipt",
            "supplier": po_a.supplier,
            "items": [
                {
                    "item_code": "TEST-DISC-001",
                    "qty": 10,
                    "rate": po_a.items[0].rate,
                    "price_list_rate": po_a.items[0].price_list_rate,
                    "warehouse": self._get_warehouse(),
                    "purchase_order": po_a.name,
                    "purchase_order_item": po_a.items[0].name,
                },
                {
                    "item_code": "TEST-DISC-002",
                    "qty": 10,
                    "rate": po_b.items[0].rate,
                    "price_list_rate": po_b.items[0].price_list_rate,
                    "warehouse": self._get_warehouse(),
                    "purchase_order": po_b.name,
                    "purchase_order_item": po_b.items[0].name,
                },
            ],
        })
        pr.insert(ignore_permissions=True)
        pr.submit()
        pr.reload()

        # Each item should be allocated from its own PO's pool
        item_a = pr.items[0]
        item_b = pr.items[1]

        po_a_discount = flt(po_a.items[0].discount_amount) * flt(po_a.items[0].qty)
        po_b_discount = flt(po_b.items[0].discount_amount) * flt(po_b.items[0].qty)

        self.assertAlmostEqual(
            flt(item_a.custom_disc_allocated_discount), po_a_discount, places=2,
        )
        self.assertAlmostEqual(
            flt(item_b.custom_disc_allocated_discount), po_b_discount, places=2,
        )

    # ──────────────────────────────────────────────────────────
    #  TEST CASE 3: Cancel/Amend
    # ──────────────────────────────────────────────────────────

    def test_cancel_and_re_receive(self):
        """Cancel first PR, then a second PR should get 100% allocation."""
        po = self._make_po(
            items=[{"item_code": "TEST-DISC-001", "qty": 100, "rate": 500000, "eligible": True}],
            discount_percentage=5.0,
        )
        total_discount = flt(po.items[0].discount_amount) * flt(po.items[0].qty)

        # PR #1: partial
        pr1 = self._make_pr(po, {"TEST-DISC-001": 60})
        pr1.submit()

        # Cancel PR #1
        pr1.cancel()

        # PR #2: full qty
        pr2 = self._make_pr(po, {"TEST-DISC-001": 100})
        pr2.submit()
        pr2.reload()

        # PR #2 should get 100% of the discount (since PR #1 is cancelled)
        self.assertAlmostEqual(
            flt(pr2.items[0].custom_disc_allocated_discount),
            total_discount,
            places=2,
        )

    # ──────────────────────────────────────────────────────────
    #  TEST CASE 4: Non-eligible items skipped
    # ──────────────────────────────────────────────────────────

    def test_non_eligible_skipped(self):
        """Items without custom_disc_eligible should not get allocation."""
        po = self._make_po(
            items=[
                {"item_code": "TEST-DISC-001", "qty": 10, "rate": 100000, "eligible": True},
                {"item_code": "TEST-DISC-002", "qty": 10, "rate": 100000, "eligible": True},
                {"item_code": "TEST-DISC-003", "qty": 10, "rate": 100000, "eligible": False},
            ],
            discount_percentage=5.0,
        )

        pr = self._make_pr(po, {
            "TEST-DISC-001": 10,
            "TEST-DISC-002": 10,
            "TEST-DISC-003": 10,
        })
        pr.submit()
        pr.reload()

        # Non-eligible item should have 0 allocated discount
        item_3 = [i for i in pr.items if i.item_code == "TEST-DISC-003"][0]
        self.assertEqual(flt(item_3.custom_disc_allocated_discount), 0)

        # Eligible items should have > 0
        item_1 = [i for i in pr.items if i.item_code == "TEST-DISC-001"][0]
        self.assertGreater(flt(item_1.custom_disc_allocated_discount), 0)

    # ──────────────────────────────────────────────────────────
    #  TEST CASE 10 & 11: Historical Entry Guard
    # ──────────────────────────────────────────────────────────

    def test_historical_entry_guard_checkbox(self):
        """When is_historical is checked, discount_amount should not be overwritten."""
        po = self._make_po(
            items=[{"item_code": "TEST-DISC-001", "qty": 10, "rate": 100000, "eligible": True}],
            discount_percentage=5.0,
        )

        pr = self._make_pr(po, {"TEST-DISC-001": 10}, is_historical=True)

        # Manually set a specific discount_amount before save
        pr.items[0].discount_amount = 999
        pr.items[0].rate = 99001  # arbitrary

        pr.save()
        pr.reload()

        # Module 1 should NOT have overwritten these values
        self.assertEqual(flt(pr.items[0].discount_amount), 999)
        self.assertEqual(flt(pr.items[0].rate), 99001)
        # No allocation log should be appended
        self.assertEqual(len(pr.custom_disc_allocation_log), 0)

    def test_historical_guard_import_flag(self):
        """When frappe.flags.in_import is set, discount should not be overwritten."""
        po = self._make_po(
            items=[{"item_code": "TEST-DISC-001", "qty": 10, "rate": 100000, "eligible": True}],
            discount_percentage=5.0,
        )

        pr = self._make_pr(po, {"TEST-DISC-001": 10})
        pr.items[0].discount_amount = 0  # explicitly zero

        # Simulate import flag
        frappe.flags.in_import = True
        try:
            pr.save()
        finally:
            frappe.flags.in_import = False

        pr.reload()

        # discount_amount should remain 0 (not recalculated)
        self.assertEqual(flt(pr.items[0].discount_amount), 0)
        self.assertEqual(len(pr.custom_disc_allocation_log), 0)

    # ──────────────────────────────────────────────────────────
    #  TEST CASE 12: Manual PR Discount Override
    # ──────────────────────────────────────────────────────────

    def test_manual_pr_discount_overridden_by_po_eligible(self):
        """When a user enters a manual discount on a PR item linked to a discount-eligible PO,
        Module 1 MUST explicitly override the manual discount with the PO proportional discount.
        """
        po = self._make_po(
            items=[{"item_code": "TEST-DISC-001", "qty": 10, "rate": 100000, "eligible": True}],
            discount_percentage=10.0,  # 10,000 per unit discount from PO pool
        )

        pr = self._make_pr(po, {"TEST-DISC-001": 10})

        # User attempts to manually enter a conflicting row discount on the PR item
        pr.items[0].custom_palma_discount_type = "Amount"
        pr.items[0].custom_palma_discount_amount = 50000  # 5,000 per unit manual attempt
        pr.items[0].discount_amount = 5000

        pr.save()
        pr.reload()

        # Module 1 MUST WIN: discount_amount must equal PO proportional allocation (10,000)
        po_allocated_per_unit = 10000.0
        self.assertEqual(
            flt(pr.items[0].discount_amount),
            po_allocated_per_unit,
            msg="Module 1 PO proportional discount must override manual PR discount for PO-linked eligible items"
        )
        self.assertEqual(flt(pr.items[0].rate), 90000.0)
        self.assertGreater(len(pr.custom_disc_allocation_log), 0)

    # ──────────────────────────────────────────────────────────
    #  TEST CASE 13: End-to-End PT XCMG Scenario
    # ──────────────────────────────────────────────────────────

    def test_e2e_xcmg_po_global_discount_module2_to_pr_module1(self):
        """Replicates PT XCMG real scenario:
          1. Create PO with 3 items using Module 2 base rates (custom_palma_base_rate)
          2. Apply Module 2 Global Discount Amount (e.g. 6,760,000 IDR) via value-weighted distribution
          3. Validate PO via purchase_order_discount.before_validate (Module 2 server fallback)
          4. Submit PO with custom_disc_eligible = 1 on items
          5. Receive PR #1 (60% qty) and PR #2 (40% qty closing receipt)
          6. Verify Module 1 pools exact discount amounts generated by Module 2, allocates 60% in PR #1
             and exact remainder in PR #2, matching total 6,760,000 IDR discount pool with 0 FP drift.
        """
        from advanced_discounting.purchase_discounting.purchase_order_discount import (
            before_validate as po_before_validate,
        )

        # 1. Create Purchase Order with custom_palma_base_rate
        po = frappe.get_doc({
            "doctype": "Purchase Order",
            "supplier": self._get_supplier(),
            "schedule_date": frappe.utils.today(),
            "custom_palma_global_disc_type": "Amount",
            "custom_palma_global_disc_value": 6760000.0,
            "items": [
                {
                    "item_code": "TEST-DISC-001",
                    "qty": 100,
                    "custom_palma_base_rate": 1000000.0,
                    "price_list_rate": 1000000.0,
                    "schedule_date": frappe.utils.today(),
                    "warehouse": self._get_warehouse(),
                    "custom_disc_eligible": 1,
                },
                {
                    "item_code": "TEST-DISC-002",
                    "qty": 100,
                    "custom_palma_base_rate": 1267600.0,
                    "price_list_rate": 1267600.0,
                    "schedule_date": frappe.utils.today(),
                    "warehouse": self._get_warehouse(),
                    "custom_disc_eligible": 1,
                },
                {
                    "item_code": "TEST-DISC-003",
                    "qty": 100,
                    "custom_palma_base_rate": 1000000.0,
                    "price_list_rate": 1000000.0,
                    "schedule_date": frappe.utils.today(),
                    "warehouse": self._get_warehouse(),
                    "custom_disc_eligible": 1,
                },
            ],
        })

        # 2. Simulate Module 2 Client-side Value-Weighted Distribution with Remainder Absorption on PO
        items = po.items
        total_amount = sum(flt(r.custom_palma_base_rate) * flt(r.qty) for r in items)  # 326,760,000
        global_disc_val = 6760000.0

        allocated_so_far = 0.0
        for idx, row in enumerate(items):
            if idx == len(items) - 1:
                # Absorbs exact remainder on last item row to eliminate FP drift
                per_row_discount = flt(global_disc_val - allocated_so_far, 2)
            else:
                row_amount = flt(row.custom_palma_base_rate) * flt(row.qty)
                per_row_discount = flt(global_disc_val * (row_amount / total_amount), 2)
                allocated_so_far += per_row_discount

            row.custom_palma_discount_type = "Amount"
            row.custom_palma_discount_amount = per_row_discount

        # 3. Trigger Module 2 Server Fallback
        po_before_validate(po, None)
        po.insert(ignore_permissions=True)
        po.submit()

        # Verify Module 2 correctly wrote discount_amount on PO item rows
        po_discount_pool_calculated = sum(
            flt(poi.discount_amount) * flt(poi.qty) for poi in po.items
        )
        self.assertAlmostEqual(po_discount_pool_calculated, 6760000.0, places=2)

        # 4. Create PR #1 (Partial - 60% of Qty)
        pr1 = self._make_pr(po, {
            "TEST-DISC-001": 60,
            "TEST-DISC-002": 60,
            "TEST-DISC-003": 60,
        })
        pr1.submit()
        pr1.reload()

        pr1_allocated = sum(flt(i.custom_disc_allocated_discount) for i in pr1.items)
        self.assertAlmostEqual(pr1_allocated, 6760000.0 * 0.6, places=2)

        # 5. Create PR #2 (Closing - remaining 40% of Qty)
        pr2 = self._make_pr(po, {
            "TEST-DISC-001": 40,
            "TEST-DISC-002": 40,
            "TEST-DISC-003": 40,
        })
        pr2.submit()
        pr2.reload()

        pr2_allocated = sum(flt(i.custom_disc_allocated_discount) for i in pr2.items)
        grand_allocated = pr1_allocated + pr2_allocated

        # 6. Final E2E Verifications:
        # Grand total allocation MUST equal exact Module 2 PO Global Discount Pool (6,760,000 IDR)
        self.assertAlmostEqual(
            grand_allocated,
            6760000.0,
            places=2,
            msg="E2E Failure: PR allocations do not equal Module 2 PO global discount pool"
        )

        # PR #2 MUST absorb remainder as closing receipt
        methods = [log.allocation_method for log in pr2.custom_disc_allocation_log]
        self.assertIn("remainder", methods)


