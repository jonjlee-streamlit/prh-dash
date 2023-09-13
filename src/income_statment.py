import pandas as pd
from .income_statement_def import INCOME_STATEMENT_DEF

def generate_income_stmt(src_df):
    # Create new column that combines Spend and Revenue Categories
    src_df = src_df.copy()
    src_df["category"] = src_df.apply(
        lambda row: row["spend_category"]
        if row["spend_category"] != ""
        else row["revenue_category"],
        axis=1,
    )

    # Start with a blank Income Statement dataframe
    income_stmt = pd.DataFrame(
        columns=[
            "hier",
            "Ledger Account",
            "Actual",
            "Budget",
            "YTD Actual",
            "YTD Budget",
        ]
    )

    # Go through each item of the income statement definition and filter and
    # add rows from the source data to the dataframe to return
    for item in INCOME_STATEMENT_DEF:
        _apply_statment_def_item(item, src_df, income_stmt, "")

    if len(src_df["dept_wd_id"].unique()) > 0:
        # When there is more than one department in the data, sum rows with the same Ledger Account.
        # Sort=False to maintain row order as they originally appear.
        income_stmt = (
            income_stmt.groupby(["hier", "Ledger Account"], sort=False, dropna=False)
            .sum()
            .reset_index()
        )

    return income_stmt


def _apply_statment_def_item(statement_def_item, src_df, income_stmt, path=""):
    """
    Process a single item in the income statement definition in the format:
    {
        "name": "Row Name",
        "items": [{"account": "40000:Patient Revenues", category: "* or Inpatient Revenue"}, ...],
        "total": ["Path/prefix/to/items/to/total", ...]
    }

    Reads data from the source data, src_df, that matches the statement definition item,
    add adds rows to the accumulator, acc, which is the dataframe to return.

    Refer to generate_income_stmt() above for the column definition for acc.
    """
    if "name" in statement_def_item and "items" in statement_def_item:
        # A header row, like Operating Revenue has a name and sub items. Update the path,
        # and recurse into child items
        if path == "":
            cur_path = statement_def_item["name"]
        else:
            cur_path = f"{path}|{statement_def_item['name']}"

        income_stmt.loc[len(income_stmt), :] = [
            cur_path,
            statement_def_item["name"],
            None,
            None,
            None,
            None,
        ]
        for sub_item in statement_def_item["items"]:
            _apply_statment_def_item(sub_item, src_df, income_stmt, cur_path)

    if "account" in statement_def_item:
        # A row with account and category. Pull in actual data from the source.
        account = statement_def_item["account"]
        category = statement_def_item.get("category")
        neg = statement_def_item.get("negative")

        if category == "*":
            # If all category, "*", get a list of categories under this Ledger Account,
            # turn this item into a header row, and pull in each category recursively.
            cur_path = f"{account}" if path == "" else f"{path}|{account}"

            # Add a header row
            income_stmt.loc[len(income_stmt), :] = [cur_path, account, None, None, None, None]

            # Get list of categories, and recursively add data
            unique_categories = set(
                src_df.loc[src_df["ledger_acct"] == account, "category"]
                .fillna("")
                .unique()
            )
            for cat in sorted(unique_categories):
                _apply_statment_def_item(
                    {"account": account, "category": cat, "negative": neg},
                    src_df,
                    income_stmt,
                    cur_path,
                )
        else:
            _add_data_from_account_and_category(account, category, neg, src_df, income_stmt, path)

    if "total" in statement_def_item:
        _add_total_row(statement_def_item, income_stmt, path)


def _add_data_from_account_and_category(account, category, neg, src_df, income_stmt, path):
    # For a specific account / category, update the current path and add all
    # matching rows from the source data.
    cur_path = f"{account}-{category}" if category is not None else account
    cur_path = cur_path if path == "" else f"{path}|{cur_path}"

    # Filter data by Ledger Account and Category if specified
    mask = src_df["ledger_acct"] == account
    if category is not None:
        mask &= src_df["category"] == category
    rows = src_df.loc[
        mask,
        ["ledger_acct", "actual", "budget", "actual_ytd", "budget_ytd"],
    ]

    # If "negative" is defined, make value negative
    multiplier = -1 if neg else 1

    # The text to display in the "Ledger Account" column should be the spend or revenue category
    # if specified, other default to the overall ledger account. If category is specified and blank,
    # make it more explicit by mapping it to the string "(Blank)"
    if category is None:
        account_text = account
    elif category == "":
        account_text = "(Blank)"
    else:
        account_text = category

    # Add each matching row into the income statement
    for _, row in rows.iterrows():
        income_stmt.loc[len(income_stmt), :] = [
            cur_path,
            account_text,
            multiplier * row["actual"],
            multiplier * row["budget"],
            multiplier * row["actual_ytd"],
            multiplier * row["budget_ytd"],
        ]


def _add_total_row(statement_def_item, income_stmt, path):
    """
    Add a row to the accumulator, acc, by adding rows already present in the dataframe.
    The rows to sum are specified in the statement definition item.
    """
    paths_to_sum = statement_def_item["total"]
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
        actual_sum = income_stmt.loc[income_stmt["hier"].str.startswith(prefix), "Actual"].sum()
        budget_sum = income_stmt.loc[income_stmt["hier"].str.startswith(prefix), "Budget"].sum()
        actual_ytd_sum = income_stmt.loc[
            income_stmt["hier"].str.startswith(prefix), "YTD Actual"
        ].sum()
        budget_ytd_sum = income_stmt.loc[
            income_stmt["hier"].str.startswith(prefix), "YTD Budget"
        ].sum()
        # Add or substract to final total
        actual += (-1 if neg else 1) * actual_sum
        budget += (-1 if neg else 1) * budget_sum
        actual_ytd += (-1 if neg else 1) * actual_ytd_sum
        budget_ytd += (-1 if neg else 1) * budget_ytd_sum

    # Update the path of the new total row to include the name of the total row
    if path == "":
        cur_path = statement_def_item["name"]
    else:
        cur_path = f"{path}|{statement_def_item['name']}"

    income_stmt.loc[len(income_stmt)] = [
        cur_path,
        statement_def_item["name"],
        actual,
        budget,
        actual_ytd,
        budget_ytd,
    ]    