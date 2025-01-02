# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import copy
import frappe
from frappe import _
from frappe.query_builder.functions import IfNull, Sum
from frappe.utils import date_diff, flt, getdate

def execute(filters=None):
    if not filters:
        return [], []

    validate_filters(filters)

    columns = get_columns(filters)
    data = get_data(filters)

    if not data:
        return [], [], None, []

    # data, chart_data = prepare_data(data, filters)

    return columns, data, None

def validate_filters(filters):
    from_date, to_date = filters.get("from_date"), filters.get("to_date")

    if not from_date and to_date:
        frappe.throw(_("From and To Dates are required."))
    elif date_diff(to_date, from_date) < 0:
        frappe.throw(_("To Date cannot be before From Date."))

def get_data(filters):
    po = frappe.qb.DocType("Purchase Order")
    po_item = frappe.qb.DocType("Purchase Order Item")
    pi_item = frappe.qb.DocType("Purchase Invoice Item")

    query = (
        frappe.qb.from_(po)
        .inner_join(po_item)
        .on(po_item.parent == po.name)
        .left_join(pi_item)
        .on((pi_item.po_detail == po_item.name) & (pi_item.docstatus == 1))
        .select(
            po.transaction_date.as_("date"),
            po_item.schedule_date.as_("required_date"),
            po_item.project,
            po.name.as_("purchase_order"),
            po.status,
            po.supplier,
            po_item.item_code,
            po_item.item_name,
            po_item.description,
            po_item.qty,
            po_item.received_qty,
            (po_item.qty - po_item.received_qty).as_("pending_qty"),
            Sum(IfNull(pi_item.qty, 0)).as_("billed_qty"),
            po_item.base_amount.as_("amount"),
            (po_item.received_qty * po_item.base_rate).as_("received_qty_amount"),
            (po_item.billed_amt * IfNull(po.conversion_rate, 1)).as_("billed_amount"),
            (po_item.base_amount - (po_item.billed_amt * IfNull(po.conversion_rate, 1))).as_(
                "pending_amount"
            ),
            po.set_warehouse.as_("warehouse"),
            po.company,
            po_item.name,
        )
        .where((po_item.parent == po.name) & (po.status.notin(("Stopped", "Closed"))) & (po.docstatus == 1))
        .groupby(po_item.name)
        .orderby(po.transaction_date)
    )

    for field in ("company", "name"):
        if filters.get(field):
            query = query.where(po[field] == filters.get(field))

    if filters.get("from_date") and filters.get("to_date"):
        query = query.where(po.transaction_date.between(filters.get("from_date"), filters.get("to_date")))

    if filters.get("status"):
        query = query.where(po.status.isin(filters.get("status")))

    if filters.get("project"):
        query = query.where(po_item.project == filters.get("project"))

    data = query.run(as_dict=True)

    # if filters.get("group_by_supplier"):
    #     grouped_data_with_totals = []
    #     seen_suppliers = set() 
    #     supplier_rows = {}

    #     for row in data:
    #         supplier = row["supplier"]
    #         if supplier not in supplier_rows:
    #             supplier_rows[supplier] = []
    #         supplier_rows[supplier].append(row)

    #     for supplier, rows in supplier_rows.items():
            
    #         if supplier not in seen_suppliers:
    #             seen_suppliers.add(supplier)
    #             rows[0]["supplier"] = supplier
    #         else:
    #             rows[0]["supplier"] = ""

    #         grouped_data_with_totals.extend(rows)

    #         totals = {
    #         "supplier": supplier + " (Total)",
    #         "qty": sum(r["qty"] for r in rows),
    #         "received_qty": sum(r["received_qty"] for r in rows),
    #         "pending_qty": sum(r["pending_qty"] for r in rows),
    #         "billed_qty": sum(r["billed_qty"] for r in rows),
    #         "amount": sum(r["amount"] for r in rows),
    #         "billed_amount": sum(r["billed_amount"] for r in rows),
    #         "pending_amount": sum(r["pending_amount"] for r in rows),
    #         "received_qty_amount": sum(r["received_qty_amount"] for r in rows),
    #         "bold": 1,
    #         }
    #         grouped_data_with_totals.append(totals)

        # return grouped_data_with_totals



    # if filters.get("group_by_supplier"):
    #     grouped_data_with_totals = []
    #     supplier_rows = {}

    #     # Group data by supplier
    #     for row in data:
    #         supplier = row["supplier"]
    #         if supplier not in supplier_rows:
    #             supplier_rows[supplier] = []
    #         supplier_rows[supplier].append(row)

    #     # Process each supplier's rows
    #     for supplier, rows in supplier_rows.items():
    #         grouped_data_with_totals.append({"supplier": supplier})  # Supplier header row

    #         # Group rows by item code within the supplier
    #         item_code_rows = {}
    #         for row in rows:
    #             item_code = row["item_code"]
    #             if item_code not in item_code_rows:
    #                 item_code_rows[item_code] = []
    #             item_code_rows[item_code].append(row)

    #         # Process each item's rows and calculate totals
    #         for item_code, item_rows in item_code_rows.items():
    #             # Add item rows
    #             for row in item_rows:
    #                 row["supplier"] = ""  # Remove supplier name for individual rows
    #                 row["item_code"] = item_code
    #                 grouped_data_with_totals.append(row)

    #             # Calculate item-wise totals
    #             totals = {
    #                 "supplier": "",
    #                 "item_code": f"{item_code} (Total)",
    #                 "qty": sum(r["qty"] for r in item_rows),
    #                 "received_qty": sum(r["received_qty"] for r in item_rows),
    #                 "pending_qty": sum(r["pending_qty"] for r in item_rows),
    #                 "billed_qty": sum(r["billed_qty"] for r in item_rows),
    #                 "amount": sum(r["amount"] for r in item_rows),
    #                 "billed_amount": sum(r["billed_amount"] for r in item_rows),
    #                 "pending_amount": sum(r["pending_amount"] for r in item_rows),
    #                 "received_qty_amount": sum(r["received_qty_amount"] for r in item_rows),
    #             }

    #             # Make the total row fields bold
    #             totals = {key: f"<b>{value}</b>" if isinstance(value, (str, int, float)) else value for key, value in totals.items()}
    #             grouped_data_with_totals.append(totals)

    #     return grouped_data_with_totals



    if filters.get("group_by_supplier"):
        grouped_data_with_totals = []
        supplier_rows = {}

        # Group data by supplier
        for row in data:
            supplier = row["supplier"]
            if supplier not in supplier_rows:
                supplier_rows[supplier] = []
            supplier_rows[supplier].append(row)

        # Process each supplier's rows
        for supplier, rows in supplier_rows.items():
            grouped_data_with_totals.append({
                "supplier": supplier,
                "item_code": "Supplier"  # This won't trigger the bold formatting
            })

            # Group rows by item code within the supplier
            item_code_rows = {}
            for row in rows:
                item_code = row["item_code"]
                if item_code not in item_code_rows:
                    item_code_rows[item_code] = []
                item_code_rows[item_code].append(row)

            # Process each item's rows and calculate totals
            for item_code, item_rows in item_code_rows.items():
                # Add item rows
                for row in item_rows:
                    row["supplier"] = ""  # Remove supplier name for individual rows
                    row["item_code"] = item_code
                    
                    grouped_data_with_totals.append(row)

                # Calculate item-wise totals
                    totals = {
                    "supplier": "",
                    "item_code": f"{item_code} (Total)",  # This will trigger bold formatting
                    "qty": sum(r["qty"] for r in item_rows),
                    "received_qty": sum(r["received_qty"] for r in item_rows),
                    "pending_qty": sum(r["pending_qty"] for r in item_rows),
                    "billed_qty": sum(r["billed_qty"] for r in item_rows),
                    "amount": sum(r["amount"] for r in item_rows),
                    "billed_amount": sum(r["billed_amount"] for r in item_rows),
                    "pending_amount": sum(r["pending_amount"] for r in item_rows),
                    "received_qty_amount": sum(r["received_qty_amount"] for r in item_rows),
                    
                }
                grouped_data_with_totals.append(totals)

        return grouped_data_with_totals



    
    if filters.get("group_by_item_code"):
        grouped_data_with_totals = []
        seen_item_codes = set()  
        item_code_rows = {}
        
        for row in data:
            item_code = row["item_code"]
            if item_code not in item_code_rows:
                item_code_rows[item_code] = []
            item_code_rows[item_code].append(row)
        
        for item_code, rows in item_code_rows.items():
            
            if item_code not in seen_item_codes:
                seen_item_codes.add(item_code)
                rows[0]["item_code"] = item_code
            else:
                rows[0]["item_code"] = ""

            for row in rows:
                row["is_bold"] = False

            grouped_data_with_totals.extend(rows)
            
            totals = {
                "item_code": item_code + " (Total)",
                "qty": sum(r["qty"] for r in rows),
                "received_qty": sum(r["received_qty"] for r in rows),
                "pending_qty": sum(r["pending_qty"] for r in rows),
                "billed_qty": sum(r["billed_qty"] for r in rows),
                "amount": sum(r["amount"] for r in rows),
                "billed_amount": sum(r["billed_amount"] for r in rows),
                "pending_amount": sum(r["pending_amount"] for r in rows),
                "received_qty_amount": sum(r["received_qty_amount"] for r in rows),
                "is_bold": True
            }
            grouped_data_with_totals.append(totals)

        return grouped_data_with_totals

    return data

# def prepare_data(data, filters):
#     completed, pending = 0, 0
#     pending_field = "pending_amount"
#     completed_field = "billed_amount"

#     for row in data:
#         completed += row[completed_field]
#         pending += row[pending_field]

#         # Prepare additional fields
#         row["qty_to_bill"] = flt(row["qty"]) - flt(row["billed_qty"])

#     chart_data = prepare_chart_data(pending, completed)

#     return data, chart_data

# def prepare_chart_data(pending, completed):
#     labels = ["Amount to Bill", "Billed Amount"]

#     return {
#         "data": {"labels": labels, "datasets": [{"values": [pending, completed]}]},
#         "type": "donut",
#         "height": 300,
#     }

def get_columns(filters):
    columns = [
        {"label": _("Date"), "fieldname": "date", "fieldtype": "Date", "width": 90},
        {"label": _("Required By"), "fieldname": "required_date", "fieldtype": "Date", "width": 90},
        {
            "label": _("Project"),
            "fieldname": "project",
            "fieldtype": "Link",
            "options": "Project",
            "width": 130,
        },
        {
            "label": _("Purchase Order"),
            "fieldname": "purchase_order",
            "fieldtype": "Link",
            "options": "Purchase Order",
            "width": 160,
        },
        {"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 130},
        {
            "label": _("Supplier"),
            "fieldname": "supplier",
            "fieldtype": "Link",
            "options": "Supplier",
            "width": 130,
        },
        
        {
                "label": _("Item Code"),
                "fieldname": "item_code",
                "fieldtype": "Link",
                "options": "Item",
                "width": 100,
        },
        {"label": _("Item Name"), "fieldname": "item_name", "fieldtype": "Data", "width": 120},
        {"label": _("Description"), "fieldname": "description", "fieldtype": "Data", "width": 120},
    ]
    columns.extend(
        [
            {
                "label": _("Qty"),
                "fieldname": "qty",
                "fieldtype": "Float",
                "width": 120,
                "convertible": "qty",
            },
            {
                "label": _("Received Qty"),
                "fieldname": "received_qty",
                "fieldtype": "Float",
                "width": 120,
                "convertible": "qty",
            },
            {
                "label": _("Pending Qty"),
                "fieldname": "pending_qty",
                "fieldtype": "Float",
                "width": 80,
                "convertible": "qty",
            },
            {
                "label": _("Billed Qty"),
                "fieldname": "billed_qty",
                "fieldtype": "Float",
                "width": 80,
                "convertible": "qty",
            },
            {
                "label": _("Qty to Bill"),
                "fieldname": "qty_to_bill",
                "fieldtype": "Float",
                "width": 80,
                "convertible": "qty",
            },
            {
                "label": _("Amount"),
                "fieldname": "amount",
                "fieldtype": "Currency",
                "width": 110,
                "options": "Company:company:default_currency",
                "convertible": "rate",
            },
            {
                "label": _("Billed Amount"),
                "fieldname": "billed_amount",
                "fieldtype": "Currency",
                "width": 110,
                "options": "Company:company:default_currency",
                "convertible": "rate",
            },
            {
                "label": _("Pending Amount"),
                "fieldname": "pending_amount",
                "fieldtype": "Currency",
                "width": 130,
                "options": "Company:company:default_currency",
                "convertible": "rate",
            },
            {
                "label": _("Received Qty Amount"),
                "fieldname": "received_qty_amount",
                "fieldtype": "Currency",
                "width": 130,
                "options": "Company:company:default_currency",
                "convertible": "rate",
            },
            {
                "label": _("Warehouse"),
                "fieldname": "warehouse",
                "fieldtype": "Link",
                "options": "Warehouse",
                "width": 100,
            },
            {
                "label": _("Company"),
                "fieldname": "company",
                "fieldtype": "Link",
                "options": "Company",
                "width": 100,
            },
        ]
    )

    return columns
