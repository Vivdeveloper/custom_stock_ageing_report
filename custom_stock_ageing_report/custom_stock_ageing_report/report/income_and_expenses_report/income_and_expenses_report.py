from datetime import datetime, timedelta
import frappe

def execute(filters=None):
    columns, branch_list = get_columns(filters)
    data = get_data(filters, branch_list)
    return columns, data

def get_columns(filters):
    branch_query = """
        SELECT DISTINCT branch 
        FROM `tabGL Entry`
        WHERE branch IS NOT NULL AND company = %(company)s
    """
    branches = frappe.db.sql(branch_query, filters, as_list=True)
    branch_list = [branch[0] for branch in branches]

    columns = [
        {"label": "Account", "fieldname": "account", "fieldtype": "Link", "options": "Account", "width": 300},
        {"label": "Total", "fieldname": "total_amount", "fieldtype": "Currency", "width": 150}
    ]

    for branch in branch_list:
        columns.append({"label": f"{branch} Amount", "fieldname": f"{branch.lower()}_amount", "fieldtype": "Currency", "width": 150})

    return columns, branch_list

def get_data(filters, branch_list):
    if not filters.get("from_date"):
        frappe.throw("Please select a 'From Date' filter.")
    if filters.get("monthwise") and not filters.get("to_date"):
        frappe.throw("Please select a 'To Date' filter for monthwise data.")
    if not filters.get("company"):
        frappe.throw("Please select a 'Company' filter.")

    conditions = "gle.company = %(company)s"
    
    if filters.get("monthwise"):
        filters["to_date"] = (datetime.strptime(filters["from_date"], "%Y-%m-%d") + timedelta(days=30)).strftime("%Y-%m-%d")
    else:
        conditions += " AND gle.posting_date BETWEEN %(from_date)s AND %(to_date)s"

    if filters.get("frequency") == "Monthly":
        conditions += " AND MONTH(gle.posting_date) = MONTH(%(from_date)s)"
    elif filters.get("frequency") == "Yearly":
        conditions += " AND YEAR(gle.posting_date) = YEAR(%(from_date)s)"

    conditions += " AND a.root_type IN ('Income', 'Expense')"

    query = f"""
        SELECT 
            gle.branch, 
            gle.account, 
            SUM(gle.debit) AS debit, 
            SUM(gle.credit) AS credit
        FROM 
            `tabGL Entry` gle
        JOIN 
            `tabAccount` a ON gle.account = a.name
        WHERE 
            {conditions}
        GROUP BY 
            gle.account, gle.branch
    """

    results = frappe.db.sql(query, filters, as_dict=True)

    accounts_query = """
        SELECT 
            name AS account, 
            parent_account, 
            is_group, 
            root_type
        FROM 
            `tabAccount`
        WHERE 
            root_type IN ('Income', 'Expense') AND company = %(company)s
    """
    accounts = frappe.db.sql(accounts_query, filters, as_dict=True)

    account_dict = {account["account"]: {**account, "total_amount": 0} for account in accounts}

    for account in account_dict.values():
        for branch in branch_list:
            account[f"{branch.lower()}_amount"] = 0

    # Process results and calculate branch totals
    for row in results:
        account = account_dict.get(row["account"])
        if account:
            branch_key = f"{row['branch'].lower()}_amount" if row["branch"] else None
            # Adjust the amount based on whether it's Income or Expense
            if account["root_type"] == "Income":
                branch_amount = row["credit"] - row["debit"]  # Income: credit - debit
            else:
                branch_amount = row["debit"] - row["credit"]  # Expense: debit - credit
            
            if branch_key:
                account[branch_key] += branch_amount
            account["total_amount"] += branch_amount

    def aggregate_values(parent):
        children = [account for account in account_dict.values() if account["parent_account"] == parent]
        parent_account = account_dict.get(parent)
        
        for child in children:
            aggregate_values(child["account"])
            
            for branch in branch_list:
                branch_key = f"{branch.lower()}_amount"
                if parent_account:
                    parent_account[branch_key] += child[branch_key]
            if parent_account:
                parent_account["total_amount"] += child["total_amount"]

    for account in account_dict.values():
        if not account["parent_account"]:
            aggregate_values(account["account"])

    # Build tree data
    def build_tree(parent, indent=0):
        children = [account for account in account_dict.values() if account["parent_account"] == parent]
        tree_data = []
        for child in sorted(children, key=lambda x: x["account"]):
            child["indent"] = indent
            tree_data.append(child)
            if child["is_group"]:
                tree_data.extend(build_tree(child["account"], indent + 1))
        return tree_data

    data = build_tree(None)

        # Initialize the total row with income - expense calculation for each branch
    totals = {"account": "Total", "total_amount": 0}
    for branch in branch_list:
        branch_key = f"{branch.lower()}_amount"
        totals[branch_key] = 0

    # Calculate totals for each branch and overall total
    for row in data:
        if not row["is_group"]:
            for branch in branch_list:
                branch_key = f"{branch.lower()}_amount"
                if branch_key in row:
                    totals[branch_key] += row[branch_key]
            totals["total_amount"] += row["total_amount"]

    # Adjust the totals to calculate overall total as income - expense
    for branch in branch_list:
        branch_income_total = sum(
            row[f"{branch.lower()}_amount"]
            for row in data
            if not row["is_group"] and account_dict[row["account"]]["root_type"] == "Income"
        )
        branch_expense_total = sum(
            row[f"{branch.lower()}_amount"]
            for row in data
            if not row["is_group"] and account_dict[row["account"]]["root_type"] == "Expense"
        )
        
        # Update the total for each branch as income - expense
        branch_key = f"{branch.lower()}_amount"
        totals[branch_key] = branch_income_total - branch_expense_total

    # Adjust overall total as income - expense
    income_total = sum(
        row["total_amount"]
        for row in data
        if not row["is_group"] and account_dict[row["account"]]["root_type"] == "Income"
    )

    expense_total = sum(
        row["total_amount"]
        for row in data
        if not row["is_group"] and account_dict[row["account"]]["root_type"] == "Expense"
    )

    # Final overall total as income - expense
    totals["total_amount"] = income_total - expense_total

    # Add totals to the data
    data.append(totals)

    return data

