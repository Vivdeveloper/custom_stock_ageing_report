# Copyright (c) 2025, sushant and contributors
# For license information, please see license.txt

# import frappe


import frappe
from frappe.utils import getdate, nowdate, date_diff


def execute(filters=None):

    # Define columns
    columns = [
        {
            "fieldname": "customer",
            "label": "Customer",
            "fieldtype": "Link",
            "options": "Customer",
            "width": 150
        },
        {
            "fieldname": "category",    
            "label": "Category",
            "fieldtype": "Link",
            "options":"Category",
            "width": 150
        },
        {
            "fieldname": "name",
            "label": "Sales Invoice",
            "fieldtype": "Data",
            "width": 150
        },
        {
            "fieldname": "credit_days_left",
            "label": "Credit Days Left",
            "fieldtype": "Data",
            "width": 150
        },
        {
            "fieldname": "outstanding_amount",
            "label": "Pending Amount",
            "fieldtype": "Currency",
            "width": 150
        },
        {
            "fieldname": "credit_limit",
            "label": "Limit (Credit Limit / Credit Days)",
            "fieldtype": "Data",
            "width": 200
}
    ]
    
    # Initialize filters to ensure no KeyError
    if not filters:
        filters = {}

    # Fetch filter values
    from_date_filter = filters.get("from_date")
    to_date_filter = filters.get("to_date")
    customer_filter = filters.get("customer")

    # Build the conditions for the database query
    conditions = []
    if from_date_filter:
        conditions.append(f"posting_date >= '{from_date_filter}'")
    if to_date_filter:
        conditions.append(f"posting_date <= '{to_date_filter}'")
    if customer_filter:
        conditions.append(f"customer = '{customer_filter}'")

    where_clause = " AND     ".join(conditions) if conditions else "1=1"


   
    sales_invoices = frappe.db.sql(
        f"""
        SELECT 
            si.customer,
            si.category,
            si.name,
            si.due_date,
            si.outstanding_amount,
            ccl.category AS credit_category,
            ccl.credit_limit_amount,
            ccl.credit_days
        FROM 
           `tabSales Invoice` AS si
        LEFT JOIN 
            `tabCustomer Credit Limit Custom` AS ccl
        ON 
            si.customer = ccl.parent AND si.category = ccl.category  -- Ensure category matches
        WHERE
            {where_clause}
        """,
        as_dict=True
    )

    # Process data to calculate credit days left
    data = []
    current_date = getdate(nowdate())  # Get today's date
    for si in sales_invoices:
        if si.due_date:
            due_date = getdate(si.due_date)
            credit_days_left = date_diff(due_date, current_date)  # Calculate days left
            if credit_days_left < 0:
                # Overdue logic with formatting
                status = f"<font color='red'>Overdue +{abs(credit_days_left)} days</font>"
            else:
                status = f"{credit_days_left} days left"
        else:
            # Handle cases with no due date
            status = "No Due Date"

        
        if si.credit_category == si.category:
            credit_limit_combined = (
                f"{si.credit_limit_amount} / {si.credit_days} days"
                if si.credit_limit_amount and si.credit_days
                else "Not Set"
            )
        else:
            credit_limit_combined = "Not Set"

        # Append processed data
        data.append({
            "customer": si.customer,
            "category": si.category,
            "name": si.name,
            "credit_days_left": status,
            "outstanding_amount": si.outstanding_amount,
            "credit_limit": credit_limit_combined
        })

    # Return the columns and processed data
    return columns, data