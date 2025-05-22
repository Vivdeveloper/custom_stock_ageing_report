import frappe
from frappe.utils import getdate, nowdate, date_diff

def execute(filters=None):
    # Initialize filters to ensure no KeyError
    if not filters:
        filters = {}

    group_by_customer = filters.get("group_by_customer", 0)

    # Define columns based on group_by_customer
    if group_by_customer:
        columns = [
            {
                "fieldname": "customer",
                "label": "Customer",
                "fieldtype": "Link",
                "options": "Customer",
                "width": 150
            },
            {
                "fieldname": "sales_person",
                "label": "Sales Person",
                "fieldtype": "Link",
                "options": "Sales Person",
                "width": 150
            },
            {
                "fieldname": "category",
                "label": "Category",
                "fieldtype": "Link",
                "options": "Category",
                "width": 150
            },
            {
                "fieldname": "name",
                "label": "Sales Invoice",
                "fieldtype": "Data",
                "width": 150
            },
            {
                "fieldname": "posting_date",
                "label": "Invoice Date",
                "fieldtype": "Date",
                "width": 150
            },
            {
                "label": "Branch",
                "fieldname": "branch",
                "fieldtype": "Link",
                "options": "Branch",
                "width": 100
            },
            {
                "fieldname": "rounded_total",
                "label": "Rounded Total",
                "fieldtype": "Currency",
                "width": 150
            },
            {
                "fieldname": "total_advance",
                "label": "Total Advance",
                "fieldtype": "Currency",
                "width": 150
            },
            {
                "fieldname": "outstanding_amount",
                "label": "Outstanding Amount",
                "fieldtype": "Currency",
                "width": 150
            }
        ]
    else:
        columns = [
            {
                "fieldname": "customer",
                "label": "Customer",
                "fieldtype": "Link",
                "options": "Customer",
                "width": 150
            },
            {
                "fieldname": "sales_person",
                "label": "Sales Person",
                "fieldtype": "Link",
                "options": "Sales Person",
                "width": 150
            },
            {
                "fieldname": "category",
                "label": "Category",
                "fieldtype": "Link",
                "options": "Category",
                "width": 150
            },
            {
                "fieldname": "name",
                "label": "Sales Invoice",
                "fieldtype": "Data",
                "width": 150
            },
            {
                "fieldname": "posting_date",
                "label": "Invoice Date",
                "fieldtype": "Date",
                "width": 150
            },
            {
                "label": "Branch",
                "fieldname": "branch",
                "fieldtype": "Link",
                "options": "Branch",
                "width": 100
            },
            {
                "fieldname": "credit_days_left",
                "label": "Credit Days Left",
                "fieldtype": "Data",
                "width": 150
            },
            {
                "fieldname": "rounded_total",
                "label": "Rounded Total",
                "fieldtype": "Currency",
                "width": 150
            },
            {
                "fieldname": "total_advance",
                "label": "Total Advance",
                "fieldtype": "Currency",
                "width": 150
            },
            {
                "fieldname": "outstanding_amount",
                "label": "Outstanding Amount",
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

    # Fetch filter values
    from_date_filter = filters.get("from_date")
    to_date_filter = filters.get("to_date")
    customer_filter = filters.get("customer")
    sales_person_filter = filters.get("sales_person")
    branch_filter = filters.get("branch")
    category_filter = filters.get("category")
    credit_days_left_filter = filters.get("credit_days_left")

    # Build the conditions for the database query
    conditions = []
    if from_date_filter:
        conditions.append(f"si.posting_date >= '{from_date_filter}'")
    if to_date_filter:
        conditions.append(f"si.posting_date <= '{to_date_filter}'")
    if customer_filter:
        conditions.append(f"si.customer = '{customer_filter}'")
    if sales_person_filter:
        conditions.append(f"st.sales_person = '{sales_person_filter}'")
    if branch_filter:
        conditions.append(f"si.branch = '{branch_filter}'")
    if category_filter:
        conditions.append(f"si.category = '{category_filter}'")
    conditions.append(f"si.status IN " + " ('Partly Paid', 'Unpaid', 'Overdue')")

    where_clause = " AND ".join(conditions) if conditions else "1=1"

    # Query to fetch sales invoices with sales person from sales_team table
    sales_invoices = frappe.db.sql(
        f"""
        SELECT 
            si.customer,
            si.customer_name,
            si.category,
            si.name,
            si.posting_date,
            si.branch,
            si.rounded_total,
            si.total_advance,
            si.outstanding_amount,
            ccl.category AS credit_category,
            ccl.credit_limit_amount,
            ccl.credit_days,
            si.due_date,
            st.sales_person
        FROM 
            `tabSales Invoice` AS si
        LEFT JOIN 
            `tabCustomer Credit Limit Custom` AS ccl
        ON 
            si.customer = ccl.parent AND si.category = ccl.category
        LEFT JOIN 
            `tabSales Team` AS st
        ON 
            si.name = st.parent AND st.parenttype = 'Sales Invoice'
        WHERE
            {where_clause}
        """,
        as_dict=True
    )

    # Process data
    data = []
    current_date = getdate(nowdate())
    for si in sales_invoices:
        # Get credit days for the category
        credit_days = si.credit_days if si.credit_days else 0
        invoice_date = getdate(si.posting_date)

        # Calculate credit days left
        if credit_days > 0:
            days_passed = date_diff(current_date, invoice_date)
            credit_days_left = credit_days - days_passed
            if credit_days_left > -1:
                status = f"{credit_days_left} days left"
                filter_match = credit_days_left_filter in ["", "Days"]
            else:
                status = f"<font color='red'>Overdue +{abs(credit_days_left)} days</font>"
                filter_match = credit_days_left_filter in ["", "Overdue"]
        else:
            credit_days_left = 0
            status = "0"
            filter_match = credit_days_left_filter in [""]

        # Apply credit_days_left filter
        if credit_days_left_filter and not filter_match:
            continue

        # When group_by_customer is checked, only include overdue invoices
        if group_by_customer and credit_days_left >= 0:
            continue

        # Calculate credit limit
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
            "customer_name": si.customer_name,
            "sales_person": si.sales_person,
            "category": si.category,
            "name": si.name,
            "posting_date": si.posting_date,
            "branch": si.branch,
            "credit_days_left": status,
            "rounded_total": si.rounded_total,
            "total_advance": si.total_advance,
            "outstanding_amount": si.outstanding_amount,
            "credit_limit": credit_limit_combined
        })

    # Handle group by customer
    result = []
    if group_by_customer:
        grouped_data = {}
        for row in data:
            cust = row["customer"]
            if cust not in grouped_data:
                grouped_data[cust] = {
                    "rows": [],
                    "outstanding_amount": 0,
                    "rounded_total": 0,
                    "total_advance": 0,
                    "customer_name": row["customer_name"]
                }
            grouped_data[cust]["rows"].append({
                "customer": row["customer"],
                "sales_person": row["sales_person"],
                "category": row["category"],
                "name": row["name"],
                "posting_date": row["posting_date"],
                "branch": row["branch"],
                "rounded_total": row["rounded_total"],
                "total_advance": row["total_advance"],
                "outstanding_amount": row["outstanding_amount"]
            })
            grouped_data[cust]["outstanding_amount"] += row["outstanding_amount"] or 0
            grouped_data[cust]["rounded_total"] += row["rounded_total"] or 0
            grouped_data[cust]["total_advance"] += row["total_advance"] or 0

        for cust, cust_data in grouped_data.items():
            result.extend(cust_data["rows"])
            total_row = {
                "customer": f"<b>{cust}</b>",
                "sales_person": "",
                "category": "",
                "name": "",
                "posting_date": "",
                "branch": "",
                "outstanding_amount": cust_data["outstanding_amount"],
                "rounded_total": cust_data["rounded_total"],
                "total_advance": cust_data["total_advance"],
            }
            result.append(total_row)
    else:
        result = data

    # Return the columns and processed data
    return columns, result