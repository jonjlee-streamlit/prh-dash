import pandas as pd
from dataclasses import dataclass, field

# Defines how to convert a table of raw revenue/expense items to a readable income statement
DEFAULT_INCOME_STATEMENT_DEF = [
    {
        "name": "Operating Revenues",
        "items": [
            {
                "name": "Inpatient",
                "items": [
                    {
                        "account": "40000:Patient Revenues",
                        "category": "Inpatient Revenue",
                        "negative": True,
                    }
                ],
            },
            {
                "name": "Outpatient",
                "items": [
                    {
                        "account": "40000:Patient Revenues",
                        "category": "Outpatient Revenue",
                        "negative": True,
                    },
                    {
                        "account": "40000:Patient Revenues",
                        "category": "Clinic Revenue",
                        "negative": True,
                    },
                ],
            },
            {
                "name": "Other",
                "items": [
                    {
                        "account": "40010:Sales Revenue",
                        "category": "Cafeteria Sales",
                        "negative": True,
                    },
                    {
                        "account": "40300:Other Operating Revenue",
                        "category": "Misc Revenue",
                        "negative": True,
                    },
                ],
            },
        ],
    },
    {
        "name": "Deductions",
        "items": [
            {"account": "49000:Contractual Adjustments"},
            {"account": "49001:Bad Debts & Write Offs"},
            {"account": "49002:Administrative Write Offs"},
        ],
    },
    {"name": "Net Revenue", "total": ["Operating Revenues", "-Deductions"]},
    {
        "name": "Expenses",
        "items": [
            {
                "name": "Salaries",
                "items": [{"account": "50000:Salaries & Wages", "category": "*"}],
            },
            {
                "name": "Employee Benefits",
                "items": [
                    {"account": "50011:Benefits-Taxes", "category": "*"},
                    {"account": "50012:Benefits-Insurance", "category": "*"},
                    {"account": "50013:Benefits-Retirement", "category": "*"},
                    {"account": "50014:Benefits-Other", "category": "*"},
                ],
            },
            {
                "name": "Professional Fees",
                "items": [
                    {
                        "account": "60220:Professional Fees",
                        "category": "Professional Fees",
                    },
                    {"account": "60221:Temp Labor", "category": "*"},
                    {"account": "60222:Locum Tenens", "category": "*"},
                ],
            },
            {
                "name": "Supplies",
                "items": [
                    {"account": "60300:Supplies", "category": "*"},
                    {"account": "60301:Inventory Adjustments", "category": "*"},
                    {"account": "60336:Pharmaceuticals", "category": "*"},
                ],
            },
            {
                "name": "Utilities",
                "items": [
                    {"account": "60500:Utilities", "category": "*"},
                ],
            },
            {
                "name": "Puchased Services",
                "items": [
                    {"account": "60600:Purchased Services", "category": "*"},
                    {"account": "60620:Maintenance", "category": "*"},
                    {"account": "60650:Software Licenses"},
                ],
            },
            {
                "name": "Rental/Leases",
                "items": [
                    {"account": "60800:Leases/Rents Operating", "category": "*"},
                ],
            },
            {
                "name": "Insurance",
                "items": [
                    {"account": "50012:Benefits-Insurance", "category": "*"},
                ],
            },
            {
                "name": "Licenses & Taxes",
                "items": [],
            },
            {
                "name": "Other Direct Expenses",
                "items": [
                    {"account": "60951:Professional Memberships", "category": "*"},
                    {"account": "60960:Other Direct Expenses", "category": "*"},
                    {"account": "60970:Travel & Education", "category": "*"},
                ],
            },
            {
                "name": "Depreciation",
                "items": [
                    {"account": "70000:Depreciation"},
                ],
            },
        ],
    },
    {"name": "Total Operating Expenses", "total": ["Expenses/"]},
    {
        "name": "Operating Margin",
        "total": ["Operating Revenues/", "-Deductions/", "-Expenses/"],
    },
]


def generate_income_stmt(src_df, statement_def=DEFAULT_INCOME_STATEMENT_DEF):
    # Create new column that combines Spend and Revenue Categories
    src_df = src_df.copy()
    src_df["category"] = src_df.apply(
        lambda row: row["spend_category"]
        if row["spend_category"] is not None
        else row["revenue_category"],
        axis=1,
    )

    # Blank Income Statement dataframe
    ret = pd.DataFrame(
        columns=[
            "hier",
            "Ledger Account",
            "Actual",
            "Budget",
            "Actual as of ",
            "Budget as of ",
        ]
    )

    def process_item(item, path):
        """
        Process a single item in the income statement definition in the format:
        {
            "name": "Row Name",
            "items": [{"account": "40000:Patient Revenues", category: "* or Inpatient Revenue"}, ...],
            "total": ["Path/prefix/to/items/to/total", ...]
        }
        """
        if "name" in item and "items" in item:
            # A header row, like Revenue. Update the path, and recurse into child items
            cur_path = item["name"] if path == "" else f"{path}|{item['name']}"
            ret.loc[len(ret)] = [cur_path, item["name"], None, None, None, None]
            for sub_item in item["items"]:
                process_item(sub_item, cur_path)

        if "account" in item:
            # A row with account/category. Pull in actual data from the source.
            account = item["account"]
            category = item.get("category")
            neg = item.get("negative")
            if category == "*":
                # If all category, "*", get a list of categories under this Ledger Account,
                # turn this item into a header row, and pull in each category recursively.
                cur_path = f"{account}" if path == "" else f"{path}|{account}"

                # Add a header row
                ret.loc[len(ret)] = [cur_path, account, None, None, None, None]

                # Get list of categories, and recursively add data
                unique_categories = set(
                    src_df.loc[src_df["ledger_acct"] == account, "category"]
                    .fillna("")
                    .unique()
                )
                for cat in sorted(unique_categories):
                    process_item({"account": account, "category": cat}, cur_path)
            else:
                # For a specific account / category, update the current path and add all
                # matching rows from the source data.
                cur_path = f"{account}-{category}" if category else account
                cur_path = cur_path if path == "" else f"{path}|{cur_path}"

                # Filter data by Ledger Account and Category if specified
                mask = src_df["ledger_acct"] == account
                if category:
                    mask &= src_df["category"] == category
                rows = src_df.loc[
                    mask,
                    ["ledger_acct", "actual", "budget", "actual_ytd", "budget_ytd"],
                ]

                # If "negative" is defined, make value negative
                multiplier = -1 if neg else 1

                # Add each matching row into the income statement
                for _, row in rows.iterrows():
                    ret.loc[len(ret)] = [
                        cur_path,
                        category if category else row["ledger_acct"],
                        multiplier * row["actual"],
                        multiplier * row["budget"],
                        multiplier * row["actual_ytd"],
                        multiplier * row["budget_ytd"],
                    ]

        if "total" in item:
            # A row representing a total. Sum the specified values by path.
            cur_path = item["name"] if path == "" else f"{path}|{item['name']}"
            paths_to_sum = item["total"]
            actual = 0
            budget = 0
            actual_ytd = 0
            budget_ytd = 0
            for prefix in paths_to_sum:
                # Replace '/' with our actual path delimiter
                prefix = prefix.replace("/", "|")
                # If prefix starts with a '-', then we will subtract instead of add to total
                neg = prefix.startswith("-")
                prefix = prefix[1:] if neg else prefix
                # Total matching rows
                actual_sum = ret.loc[ret["hier"].str.startswith(prefix), "Actual"].sum()
                budget_sum = ret.loc[ret["hier"].str.startswith(prefix), "Budget"].sum()
                actual_ytd_sum = ret.loc[
                    ret["hier"].str.startswith(prefix), "Actual as of "
                ].sum()
                budget_ytd_sum = ret.loc[
                    ret["hier"].str.startswith(prefix), "Budget as of "
                ].sum()
                # Add or substract to final total
                actual += (-1 if neg else 1) * actual_sum
                budget += (-1 if neg else 1) * budget_sum
                actual_ytd += (-1 if neg else 1) * actual_ytd_sum
                budget_ytd += (-1 if neg else 1) * budget_ytd_sum

            ret.loc[len(ret)] = [
                cur_path,
                item["name"],
                actual,
                budget,
                actual_ytd,
                budget_ytd,
            ]

    # Return a dataframe using the given income statement definition
    for item in statement_def:
        process_item(item, "")
    return ret
