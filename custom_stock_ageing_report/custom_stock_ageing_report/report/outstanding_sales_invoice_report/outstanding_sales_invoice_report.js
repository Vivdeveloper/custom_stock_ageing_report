frappe.query_reports["Outstanding Sales Invoice Report"] = {
    "filters": [
        {
            "fieldname": "from_date",
            "label": __("From Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.add_months(frappe.datetime.get_today(), -1),
            "reqd": 0
        },
        {
            "fieldname": "to_date",
            "label": __("To Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.get_today(),
            "reqd": 0
        },
        {
            "fieldname": "customer",
            "label": __("Customer"),
            "fieldtype": "Link",
            "options": "Customer",
            "reqd": 0
        },
        {
            "fieldname": "sales_person",
            "label": __("Sales Person"),
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
            "fieldname": "category",
            "label": __("Category"),
            "fieldtype": "Link",
            "options": "Category",
            "reqd": 0
        },
        {
            "fieldname": "credit_days_left",
            "label": __("Credit Days Left"),
            "fieldtype": "Select",
            "options": ["", "Days", "Overdue"],
            "reqd": 0
        },
        {
            "fieldname": "group_by_category",
            "label": __("Group by Category"),
            "fieldtype": "Check",
            "default": 0
        }
    ],
    "formatter": function(value, row, column, data, default_formatter) {
        // Use default formatter for most cases
        value = default_formatter(value, row, column, data);

        // Apply custom formatting for specific columns when group_by_category is enabled
        if (frappe.query_report.get_filter_value("group_by_category")) {
            // Identify total rows (empty customer, sales_person, and name)
            const is_total_row = data && !data.customer && !data.sales_person && !data.name;

            // Columns to apply bold formatting and background
            const html_columns = ["category", "rounded_total", "total_advance", "outstanding_amount"];

            if (html_columns.includes(column.fieldname) && is_total_row) {
                // Ensure bold styling and add background for total row
                return `<span style="font-weight: bold; background-color: #f0f0f0;">${value}</span>`;
            }
        }

        return value;
    },
    "onload": function(report) {
        // Get the group_by_category and sales_person filters
        const group_by_category_filter = report.get_filter("group_by_category");
        const sales_person_filter = report.get_filter("sales_person");

        // Function to toggle sales_person filter visibility
        function toggle_sales_person_filter() {
            const group_by_category = group_by_category_filter.get_value();
            if (group_by_category) {
                // Hide sales_person filter when group_by_category is checked
                sales_person_filter.$wrapper.hide();
                // Optionally clear the sales_person filter value
                sales_person_filter.set_value("");
            } else {
                // Show sales_person filter when group_by_category is unchecked
                sales_person_filter.$wrapper.show();
            }
        }

        // Initial toggle based on default value
        toggle_sales_person_filter();

        // Add onchange listener to group_by_category filter
        group_by_category_filter.$input.on("change", function() {
            toggle_sales_person_filter();
            // Refresh the report to apply filter changes
            report.refresh();
        });
    }
};