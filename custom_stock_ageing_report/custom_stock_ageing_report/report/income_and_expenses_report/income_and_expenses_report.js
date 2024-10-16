frappe.query_reports["Income and Expenses Report"] = {
	"filters": [
		{
			"fieldname": "from_date",
			"label": "From Date",
			"fieldtype": "Date",
			"default": "2023-01-01",
			"reqd": 1
		},
		{
			"fieldname": "to_date",
			"label": "To Date",
			"fieldtype": "Date",
			"default": "2023-12-31",
			"reqd": 1
		},
		{
			"fieldname": "frequency",
			"label": "Frequency",
			"fieldtype": "Select",
			"options": ["Monthly", "Yearly"],
			"default": "Monthly",
			"reqd": 1
		},
		{
			"fieldname": "monthwise",
			"label": "Monthwise",
			"fieldtype": "Check",
			"default": 0,
			"on_change": function() {
				
				let monthwise_checked = frappe.query_report.get_filter_value('monthwise');
				
				if (monthwise_checked) {
					frappe.query_report.toggle_filter_display('to_date', true);
					frappe.query_report.set_filter_value('frequency', 'Monthly');
				} else {
					frappe.query_report.toggle_filter_display('to_date', false);
				}
			}
		}
	]
};
