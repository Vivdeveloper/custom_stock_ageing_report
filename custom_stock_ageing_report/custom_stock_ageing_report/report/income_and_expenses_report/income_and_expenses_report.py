import frappe
from datetime import datetime, timedelta

def execute(filters=None):
    columns, branch_list = get_columns(filters)
    data = get_data(filters, branch_list)
    return columns, data

def get_columns(filters):
    # Get unique branches from GL Entries for the given company
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
    if not filters.get("to_date"):
        frappe.throw("Please select a 'To Date' filter.")
    if not filters.get("company"):
        frappe.throw("Please select a 'Company' filter.")

    conditions = build_conditions(filters)

    # Fetch GL data
    query = f"""
        SELECT 
            gle.branch, 
            gle.account, 
            gle.debit, 
            gle.credit,
            a.root_type
        FROM 
            `tabGL Entry` gle
        JOIN 
            `tabAccount` a ON gle.account = a.name
        WHERE 
            {conditions}
            AND a.root_type IN ('Income', 'Expense')
    """
    results = frappe.db.sql(query, filters, as_dict=True)

    # Fetch account structure
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

    # Populate amounts per account and branch
    for row in results:
        account = account_dict.get(row["account"])
        if account:
            branch_key = f"{row['branch'].lower()}_amount" if row["branch"] else None
            if row["root_type"] == "Income":
                amount = row["credit"] - row["debit"]
            else:
                amount = row["debit"] - row["credit"]

            if branch_key:
                account[branch_key] += amount
            account["total_amount"] += amount

    # Aggregate group accounts
    def aggregate_values(parent):
        children = [a for a in account_dict.values() if a["parent_account"] == parent]
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

    # Build tree structure
    def build_tree(parent, indent=0):
        children = [
            account for account in account_dict.values() if account["parent_account"] == parent
        ]
        children.sort(key=lambda x: (0 if x["root_type"] == "Income" else 1, x["account"]))

        tree_data = []
        for child in children:
            child["indent"] = indent
            tree_data.append(child)
            if child["is_group"]:
                tree_data.extend(build_tree(child["account"], indent + 1))
        return tree_data

    data = build_tree(None)

    # Build totals row
    totals = {"account": "Total", "total_amount": 0}
    for branch in branch_list:
        totals[f"{branch.lower()}_amount"] = 0

    for branch in branch_list:
        income = sum(
            row[f"{branch.lower()}_amount"]
            for row in data if not row["is_group"] and account_dict[row["account"]]["root_type"] == "Income"
        )
        expense = sum(
            row[f"{branch.lower()}_amount"]
            for row in data if not row["is_group"] and account_dict[row["account"]]["root_type"] == "Expense"
        )
        totals[f"{branch.lower()}_amount"] = income - expense

    total_income = sum(
        row["total_amount"] for row in data if row["root_type"] == "Income" and not row["is_group"]
    )
    total_expense = sum(
        row["total_amount"] for row in data if row["root_type"] == "Expense" and not row["is_group"]
    )

    totals["total_amount"] = total_income - total_expense

    data.append(totals)

    return data

def build_conditions(filters):
    conditions = []
    if filters.get("company"):
        conditions.append("gle.company = %(company)s")
    if filters.get("from_date"):
        conditions.append("gle.posting_date >= %(from_date)s")
    if filters.get("to_date"):
        conditions.append("gle.posting_date <= %(to_date)s")

    # DO NOT restrict to specific YEAR or MONTH when using full date ranges
    # Frequency is for grouping, not filtering

    return " AND ".join(conditions)

