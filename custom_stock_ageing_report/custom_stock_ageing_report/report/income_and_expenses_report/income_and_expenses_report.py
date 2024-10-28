import frappe
from datetime import datetime, timedelta  # Corrected import

def execute(filters=None):
    columns, branch_list = get_columns()
    data = get_data(filters, branch_list)
    return columns, data

def get_columns():
    # Fetch distinct branch names from GL Entry
    branch_query = """
        SELECT DISTINCT branch 
        FROM `tabGL Entry`
        WHERE branch IS NOT NULL
    """
    branches = frappe.db.sql(branch_query, as_list=True)
    branch_list = [branch[0] for branch in branches]  # Flatten the list

    # Define columns
    columns = [
        {"label": "Account", "fieldname": "account", "fieldtype": "Link", "options": "Account", "width": 300},
        {"label": "Account Type", "fieldname": "root_type", "fieldtype": "Data", "width": 150}
    ]

    # Dynamically add debit/credit columns for each branch
    for branch in branch_list:
        columns.append({"label": f"{branch} Debit", "fieldname": f"{branch.lower()}_debit", "fieldtype": "Currency", "width": 150})
        columns.append({"label": f"{branch} Credit", "fieldname": f"{branch.lower()}_credit", "fieldtype": "Currency", "width": 150})

    return columns, branch_list
    
def get_data(filters, branch_list):
    if not filters.get("from_date") or (filters.get("monthwise") and not filters.get("to_date")):
        frappe.throw("Please select appropriate filters for From Date and To Date.")

    conditions = ""

    # Set to_date if monthwise option is selected
    if filters.get("monthwise"):
        filters["to_date"] = (datetime.strptime(filters["from_date"], "%Y-%m-%d") + timedelta(days=30)).strftime("%Y-%m-%d")
    else:
        conditions += " AND gle.posting_date >= %(from_date)s AND gle.posting_date <= %(to_date)s"

    # Filter by frequency (monthly or yearly)
    if filters.get("frequency") == "Monthly":
        conditions += " AND MONTH(gle.posting_date) = MONTH(%(from_date)s)"
    elif filters.get("frequency") == "Yearly":
        conditions += " AND YEAR(gle.posting_date) = YEAR(%(from_date)s)"

    # Query to fetch data grouped by account and branch
    query = """
        SELECT 
            gle.branch, 
            gle.account, 
            a.root_type, 
            SUM(gle.debit) AS debit, 
            SUM(gle.credit) AS credit
        FROM 
            `tabGL Entry` gle
        JOIN 
            `tabAccount` a ON gle.account = a.name
        WHERE 
            a.root_type IN ('Income', 'Expense')
            {conditions}
        GROUP BY 
            gle.account, gle.branch
        ORDER BY 
            gle.account ASC
    """.format(conditions=conditions)

    results = frappe.db.sql(query, filters, as_dict=True)

    # Initialize data with account and blank debit/credit columns for each branch
    data_dict = {}

    for row in results:
        account_key = row['account']  # Unique key for each account

        if account_key not in data_dict:
            # Initialize a new row with default values
            data_dict[account_key] = {
                "account": row['account'],
                "root_type": row['root_type']
            }
            # Initialize debit/credit values for all branches
            for branch in branch_list:
                data_dict[account_key][f"{branch.lower()}_debit"] = 0
                data_dict[account_key][f"{branch.lower()}_credit"] = 0

        # Check if branch exists before proceeding
        if row['branch']:
            branch_key_debit = f"{row['branch'].lower()}_debit"
            branch_key_credit = f"{row['branch'].lower()}_credit"

            # Populate debit/credit values for the specific branch
            data_dict[account_key][branch_key_debit] += row['debit']
            data_dict[account_key][branch_key_credit] += row['credit']

    # Convert data dictionary to a list
    data = list(data_dict.values())

    return data
