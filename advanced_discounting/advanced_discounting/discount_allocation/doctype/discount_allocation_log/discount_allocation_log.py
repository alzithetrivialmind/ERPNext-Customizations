# Copyright (c) 2026, Palma Progress Shipyard and contributors
# For license information, please see license.txt

from frappe.model.document import Document


class DiscountAllocationLog(Document):
    """Child-table row recording one proportional discount allocation
    from a Purchase Order to a Purchase Receipt item."""

    pass
