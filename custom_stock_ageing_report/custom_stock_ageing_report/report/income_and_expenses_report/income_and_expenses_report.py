import frappe
from datetime import datetime, timedelta

def execute(filters=None):
    columns = get_columns()

    data = get_data(filters)

    return columns, data

def get_columns():
    return [
        {"label": "Account", "fieldname": "account", "fieldtype": "Link", "options": "Account", "width": 300},
        {"label": "Account Type", "fieldname": "root_type", "fieldtype": "Data", "width": 150},
        {"label": "Posting Date", "fieldname": "posting_date", "fieldtype": "Date", "width": 120},
        {"label": "Debit", "fieldname": "debit", "fieldtype": "Currency", "width": 150},
        {"label": "Credit", "fieldname": "credit", "fieldtype": "Currency", "width": 150}
    ]

def get_data(filters):
    if not filters.get("from_date") or (filters.get("monthwise") and not filters.get("to_date")):
        frappe.throw("Please select appropriate filters for From Date and To Date.")

    
    conditions = ""
    

    if filters.get("monthwise"):
        filters["to_date"] = (datetime.strptime(filters["from_date"], "%Y-%m-%d") + timedelta(days=30)).strftime("%Y-%m-%d")
    else:
        conditions += " AND gle.posting_date >= %(from_date)s AND gle.posting_date <= %(to_date)s"
    
  
    if filters.get("frequency") == "Monthly":
        conditions += " AND MONTH(gle.posting_date) = MONTH(%(from_date)s)"
    elif filters.get("frequency") == "Yearly":
        conditions += " AND YEAR(gle.posting_date) = YEAR(%(from_date)s)"
    
 
    query = """
        SELECT 
            gle.account, 
            a.root_type, 
            gle.posting_date, 
            gle.debit, 
            gle.credit
        FROM 
            `tabGL Entry` gle
        JOIN 
            `tabAccount` a ON gle.account = a.name
        WHERE 
            a.root_type IN ('Income', 'Expense')
            {conditions}
        ORDER BY 
            gle.posting_date ASC
    """.format(conditions=conditions)

    results = frappe.db.sql(query, filters, as_dict=True)

    data = []
    for row in results:
        data.append(row)
    
    return data
