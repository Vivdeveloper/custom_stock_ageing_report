// Copyright (c) 2024, sushant and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Custom Item Shortage Report"] = {
	filters: [
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			width: "80",
			options: "Company",
			reqd: 1,
			default: frappe.defaults.get_default("company"),
		},
		{
			fieldname: "warehouse",
			label: __("Warehouse"),
			fieldtype: "MultiSelectList",
			width: "100",
			get_data: function (txt) {
				return frappe.db.get_link_options("Warehouse", txt);
			},
		},
		{
			fieldname: "item_group",
			label: __("Item Group"),
			fieldtype: "MultiSelectList",
			width: "100",
			get_data: function (txt) {
				return frappe.db.get_link_options("Item Group", txt);
			},
		},
	],
};
