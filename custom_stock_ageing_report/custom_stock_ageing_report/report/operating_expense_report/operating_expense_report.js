// Copyright (c) 2024, sushant and contributors
// For license information, please see license.txt

// frappe.query_reports["Operating Expense report"] = {
	

frappe.require("assets/erpnext/js/financial_statements.js", function () {
	frappe.query_reports["Operating Expense report"] = $.extend({}, erpnext.financial_statements);

	erpnext.utils.add_dimensions("Operating Expense report", 10);

	frappe.query_reports["Operating Expense report"]["filters"].push({
		fieldname: "selected_view",
		label: __("Select View"),
		fieldtype: "Select",
		options: [
			{ value: "Report", label: __("Report View") },
			{ value: "Growth", label: __("Growth View") },
			{ value: "Margin", label: __("Margin View") },
		],
		default: "Report",
		reqd: 1,
	});

	frappe.query_reports["Operating Expense report"]["filters"].push({
		fieldname: "include_default_book_entries",
		label: __("Include Default Book Entries"),
		fieldtype: "Check",
		default: 1,
	});
});

frappe.query_reports["Operating Expense report"]["filters"].push({
	fieldname: "include_default_book_entries",
	label: __("Include Default FB Entries"),
	fieldtype: "Check",
	default: 1,
});
