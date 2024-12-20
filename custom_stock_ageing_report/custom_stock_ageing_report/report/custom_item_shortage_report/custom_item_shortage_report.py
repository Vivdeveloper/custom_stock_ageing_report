import frappe
from frappe import _

from frappe.query_builder.functions import Sum

def execute(filters=None):
    columns = get_columns()
    bin_data = get_bin_data(filters)   # Query 1: Bin, Item, Warehouse
    po_data = get_po_data(filters)     # Query 2: PO and POI data

    if not bin_data:
        return [], [], None, []

    combined_data = merge_data(bin_data, po_data)
    chart_data = get_chart_data(combined_data)

    return columns, combined_data, None, chart_data

def get_bin_data(filters):
    bin = frappe.qb.DocType("Bin")
    wh = frappe.qb.DocType("Warehouse")
    item = frappe.qb.DocType("Item")

    query = (
        frappe.qb.from_(bin)
        .left_join(wh).on(wh.name == bin.warehouse)
        .left_join(item).on(item.name == bin.item_code)
        .select(
            bin.warehouse,
            bin.item_code,
            bin.actual_qty,
            bin.ordered_qty,
            bin.projected_qty,
            bin.reserved_qty,
            wh.company,
            item.item_name,
            item.description,
            item.item_group
        )
        .where(
			(item.disabled == 0)
			& (bin.projected_qty < 0)
			& (wh.name == bin.warehouse)
			& (bin.item_code == item.name)
		)
		.orderby(bin.projected_qty)
	)

    if filters.get("warehouse"):
        query = query.where(bin.warehouse.isin(filters.get("warehouse")))

    if filters.get("company"):
        query = query.where(wh.company == filters.get("company"))

    if filters.get("item_group"):
        query = query.where(item.item_group.isin(filters.get("item_group")))

    return query.run(as_dict=True)

def get_po_data(filters):
    bin = frappe.qb.DocType("Bin")
    poi = frappe.qb.DocType("Purchase Order Item")
    po = frappe.qb.DocType("Purchase Order")

    query = (
        frappe.qb.from_(bin)
        .left_join(poi).on(poi.item_code == bin.item_code)
        .left_join(po).on(po.name == poi.parent)
        .select(
            bin.warehouse,
            bin.item_code,
            bin.ordered_qty,
            Sum(poi.received_qty).as_("total_received_qty"),
            Sum(poi.returned_qty).as_("total_returned_qty"),
            (bin.ordered_qty - (Sum(poi.received_qty) - Sum(poi.returned_qty))).as_("backorder_qty"),
        )
        .where(po.docstatus == 1)
        .groupby(bin.warehouse, bin.item_code, bin.ordered_qty)
    )

    return query.run(as_dict=True)

def merge_data(bin_data, po_data):
    # Convert PO data into a dictionary for faster lookup
    po_dict = {row["item_code"]: row for row in po_data}

    # Combine Bin data with PO data
    for row in bin_data:
        item_code = row.get("item_code")
        po_row = po_dict.get(item_code, {})
        received_qty = po_row.get("total_received_qty", 0)
        returned_qty = po_row.get("total_returned_qty", 0)
        backorder_qty = row["ordered_qty"] - (received_qty - returned_qty)
        row["received_qty"] = received_qty
        row["returned_qty"] = returned_qty
        row["backorder_qty"] = backorder_qty
    return bin_data

def get_chart_data(data):
    labels, datapoints = [], []

    for row in data:
        labels.append(row.get("item_code"))
        datapoints.append(row.get("projected_qty"))

    if len(data) > 10:
        labels = labels[:10]
        datapoints = datapoints[:10]

    return {
        "data": {"labels": labels, "datasets": [{"name": _("Projected Qty"), "values": datapoints}]},
        "type": "bar",
    }

def get_columns():
    columns = [
        {"label": _("Warehouse"), "fieldname": "warehouse", "fieldtype": "Link", "options": "Warehouse", "width": 150},
        {"label": _("Item"), "fieldname": "item_code", "fieldtype": "Link", "options": "Item", "width": 150},
        {"label": _("Actual Quantity"), "fieldname": "actual_qty", "fieldtype": "Float", "width": 120},
        {"label": _("Backorder Quantity"), "fieldname": "ordered_qty", "fieldtype": "Float", "width": 120},
        
        {"label": _("Reserved Quantity"), "fieldname": "reserved_qty", "fieldtype": "Float", "width": 120},
        {"label": _("Projected Quantity"), "fieldname": "projected_qty", "fieldtype": "Float", "width": 120},
        
        {"label": _("Company"), "fieldname": "company", "fieldtype": "Link", "options": "Company", "width": 120},
        {"label": _("Item Name"), "fieldname": "item_name", "fieldtype": "Data", "width": 100},
        {"label": _("Description"), "fieldname": "description", "fieldtype": "Data", "width": 120},
        {"label": _("Item Group"), "fieldname": "item_group", "fieldtype": "Link", "options": "Item Group", "width": 120},
    ]
    return columns
