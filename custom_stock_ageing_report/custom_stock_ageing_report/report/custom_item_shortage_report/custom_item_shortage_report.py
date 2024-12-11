import frappe
from frappe import _

from collections import defaultdict


def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)

    if not data:
        return [], [], None, []

    chart_data = get_chart_data(data)

    return columns, data, None, chart_data

def get_data(filters):
    bin = frappe.qb.DocType("Bin")
    wh = frappe.qb.DocType("Warehouse")
    item = frappe.qb.DocType("Item")
    poi = frappe.qb.DocType("Purchase Order Item")
    po = frappe.qb.DocType("Purchase Order")

    query = (
        frappe.qb.from_(bin)
        .left_join(wh).on(wh.name == bin.warehouse)
        .left_join(item).on(item.name == bin.item_code)
        .left_join(poi).on(poi.item_code == bin.item_code)
        .left_join(po).on(po.name == poi.parent)
        .select(
            bin.warehouse,
            bin.item_code,
            bin.actual_qty,
            bin.ordered_qty,
            (bin.ordered_qty - (poi.received_qty - poi.returned_qty)).as_("backorder_qty"),
            bin.planned_qty,
            bin.reserved_qty,
            bin.reserved_qty_for_production,
            bin.projected_qty,
            wh.company,
            item.item_name,
            item.description,
            item.item_group,
        )
        .where(
            (item.disabled == 0)
            & (bin.projected_qty < 0)
            & (po.docstatus == 1)
        )
        .orderby(bin.projected_qty)
    )

    if filters.get("warehouse"):
        query = query.where(bin.warehouse.isin(filters.get("warehouse")))

    if filters.get("company"):
        query = query.where(wh.company == filters.get("company"))

    if filters.get("item_group"):
        query = query.where(item.item_group.isin(filters.get("item_group")))

    raw_data = query.run(as_dict=True)

    return aggregate_data(raw_data)

def aggregate_data(raw_data):
    aggregated = defaultdict(lambda: defaultdict(float))
    grouped_data = []

    for row in raw_data:
        key = (row["warehouse"], row["item_code"])
        if key not in aggregated:
            aggregated[key] = row
        else:
            # Aggregate numeric fields
            aggregated[key]["actual_qty"] += row.get("actual_qty", 0)
            aggregated[key]["ordered_qty"] += row.get("ordered_qty", 0)
            aggregated[key]["backorder_qty"] += row.get("backorder_qty", 0)
            aggregated[key]["planned_qty"] += row.get("planned_qty", 0)
            aggregated[key]["reserved_qty"] += row.get("reserved_qty", 0)
            aggregated[key]["reserved_qty_for_production"] += row.get("reserved_qty_for_production", 0)
            aggregated[key]["projected_qty"] += row.get("projected_qty", 0)

    # Convert aggregated dictionary to a list
    grouped_data = list(aggregated.values())
    return grouped_data





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
        {
            "label": _("Warehouse"),
            "fieldname": "warehouse",
            "fieldtype": "Link",
            "options": "Warehouse",
            "width": 150,
        },
        {
            "label": _("Item"),
            "fieldname": "item_code",
            "fieldtype": "Link",
            "options": "Item",
            "width": 150,
        },
        {
            "label": _("Actual Quantity"),
            "fieldname": "actual_qty",
            "fieldtype": "Float",
            "width": 120,
            "convertible": "qty",
        },
        {
            "label": _("Ordered Quantity"),
            "fieldname": "ordered_qty",
            "fieldtype": "Float",
            "width": 120,
            "convertible": "qty",
        },
        {
            "label": _("Backorder Quantity"),
            "fieldname": "backorder_qty",
            "fieldtype": "Float",
            "width": 120,
            "convertible": "qty",
        },
        {
            "label": _("Reserved Quantity"),
            "fieldname": "reserved_qty",
            "fieldtype": "Float",
            "width": 120,
            "convertible": "qty",
        },
        
        {
            "label": _("Projected Quantity"),
            "fieldname": "projected_qty",
            "fieldtype": "Float",
            "width": 120,
            "convertible": "qty",
        },
        {
            "label": _("Received Quantity"),
            "fieldname": "received_qty",
            "fieldtype": "Float",
            "width": 120,
            "convertible": "qty",
        },
        {
            "label": _("Returned Quantity"),
            "fieldname": "returned_qty",
            "fieldtype": "Float",
            "width": 120,
            "convertible": "qty",
        },
        
        {
            "label": _("Company"),
            "fieldname": "company",
            "fieldtype": "Link",
            "options": "Company",
            "width": 120,
        },
        {
            "label": _("Item Name"),
            "fieldname": "item_name",
            "fieldtype": "Data",
            "width": 100,
        },
        {
            "label": _("Description"),
            "fieldname": "description",
            "fieldtype": "Data",
            "width": 120,
        },
        {
            "label": _("Item Group"),
            "fieldname": "item_group",
            "fieldtype": "Link",
            "options": "Item Group",
            "width": 120,
        },
    ]

    return columns
