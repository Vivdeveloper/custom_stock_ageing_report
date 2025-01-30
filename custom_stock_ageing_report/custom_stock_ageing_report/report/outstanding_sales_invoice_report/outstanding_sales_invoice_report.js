// Copyright (c) 2025, sushant and contributors
// For license information, please see license.txt

frappe.query_reports["Outstanding Sales Invoice Report"] = {
	"filters": [
		{
            "fieldname": "from_date",
            "label": __("From Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.month_start(), // Default to the first day of the current month
            "reqd": 1 // Make it mandatory
        },
        {
            "fieldname": "to_date",
            "label": __("To Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.month_end(), // Default to the last day of the current month
            "reqd": 1 // Make it mandatory
        },
        {
            "fieldname": "customer",
            "label": __("Customer Name"),
            "fieldtype": "Link",
            "options": "Customer", // Links to the Customer doctype
            "reqd": 0 // Optional filter
        }
	]
};
