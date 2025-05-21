frappe.query_reports["Outstanding Sales Invoice Report"] = {
	"filters": [
		{
			"fieldname": "from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.month_start(),
			"reqd": 1
		},
		{
			"fieldname": "to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.month_end(),
			"reqd": 1
		},
		{
			"fieldname": "customer",
			"label": __("Customer Name"),
			"fieldtype": "Link",
			"options": "Customer",
			"reqd": 0
		},
		{
			"fieldname": "sales_person",
			"label": __("Sales Person Name"),
			"fieldtype": "Link",
			"options": "Sales Person",
			"reqd": 0
		},
		{
			"fieldname": "branch",
			"label": __("Branch"),
			"fieldtype": "Link",
			"options": "Branch",
			"reqd": 0
		},
		{
			"fieldname": "credit_days_left",
			"label": __("Credit Days Left"),
			"fieldtype": "Select",
			"options": "\nDays\nOverdue",
			"reqd": 0
		},
		{
			"fieldname": "category",
			"label": __("Category"),
			"fieldtype": "Link",
			"options": "Category",
			"reqd": 0
		},
		{
			"fieldname": "group_by_customer",
			"label": __("Group by Customer"),
			"fieldtype": "Check",
			"default": 0
		}
		
	]
};


