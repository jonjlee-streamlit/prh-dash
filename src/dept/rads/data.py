import pandas as pd
from dataclasses import dataclass
from ...RawData import RawData
from ...IncomeStatement import IncomeStatement
import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder, ColumnsAutoSizeMode, JsCode

# Dict used to normalize various identifiers for the same department
DEPT_CT = "CT"
DEPT_MRI = "MRI"
DEPT_SERVICES = "SERVICES"
DEPT_ULTRASOUND = "ULTRASOUND"
DEPT_MAMMOGRAPHY = "MAMMOGRAPHY"
DEPT_NUCLEAR = "NUCLEAR"
DEPT_ID_MAP = {
    "CT Scan": DEPT_CT,
    "PRH CT SCAN": DEPT_CT,
    "CC_71300": DEPT_CT,
    "MRI": DEPT_MRI,
    "PRH MRI": DEPT_MRI,
    "CC_71200": DEPT_MRI,
    "Imaging Services": DEPT_SERVICES,
    "PRH IMAGING SERVICES": DEPT_SERVICES,
    "CC_71400": DEPT_SERVICES,
    "Ultrasound": DEPT_ULTRASOUND,
    "PRH ULTRASOUND": DEPT_ULTRASOUND,
    "CC_71430": DEPT_ULTRASOUND,
    "Mammography": DEPT_MAMMOGRAPHY,
    "PRH MAMMOGRAPHY": DEPT_MAMMOGRAPHY,
    "CC_71450": DEPT_MAMMOGRAPHY,
    "Nuclear Medicine": DEPT_NUCLEAR,
    "PRH NUCLEAR MEDICINE": DEPT_NUCLEAR,
    "CC_71600": DEPT_NUCLEAR,
}

# Income statement definition
INCOME_STATEMENT_DEF = [
    {
        "name": "Operating Revenues",
        "style": "bold",
        "items": [
            {
                "name": "Inpatient",
                "items": [
                    {
                        "account": "40000:Patient Revenues",
                        "category": "Inpatient Revenue",
                    }
                ],
            },
            {
                "name": "Outpatient",
                "items": [
                    {
                        "account": "40000:Patient Revenues",
                        "category": "Outpatient Revenue",
                    },
                    {"account": "40000:Patient Revenues", "category": "Clinic Revenue"},
                ],
            },
            {
                "name": "Total Patient Revenue",
                "total": [
                    "Operating Revenues/Inpatient",
                    "Operating Revenues/Outpatient",
                ],
            },
            {
                "name": "Other",
                "items": [
                    {"account": "40010:Sales Revenue", "category": "Cafeteria Sales"},
                    {
                        "account": "40300:Other Operating Revenue",
                        "category": "Misc Revenue",
                    },
                ],
            },
            {
                "name": "Total Revenue",
                "style": "bold",
                "total": [
                    "Operating Revenues/Inpatient",
                    "Operating Revenues/Outpatient",
                    "Operating Revenues/Other",
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
    {
        "name": "Expenses",
        "style": "bold",
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
]

REVENUE_ACCOUNTS = [
    "40000:Patient Revenues",
    "40010:Sales Revenue",
    "40300:Other Operating Revenue",
]
DEDUCTION_ACCOUNTS = [
    "49000:Contractual Adjustments",
    "49001:Bad Debts & Write Offs",
    "49002:Administrative Write Offs",
]
EXPENSE_ACCOUNTS = [
    "50000:Salaries & Wages",
    "50011:Benefits-Taxes",
    "50012:Benefits-Insurance",
    "50013:Benefits-Retirement",
    "50014:Benefits-Other",
    "60220:Professional Fees",
    "60221:Temp Labor",
    "60222:Locum Tenens",
    "60300:Supplies",
    "60336:Pharmaceuticals",
    "60500:Utilities",
    "60600:Purchased Services",
    "60620:Maintenance",
    "60650:Software Licenses",
    "60800:Leases/Rents Operating",
    "60951:Professional Memberships",
    "60960:Other Direct Expenses",
    "60970:Travel & Education",
    "61003:Licensing Fees State",
    "70000:Depreciation",
]


@dataclass
class RadsData:
    """Represents processed department specific data"""

    # Original data set
    raw: RawData

    # Income statement filtered by department
    income_stmt_by_dept: dict[IncomeStatement]

    # Calculated statistics
    stats: dict


def process(raw: RawData) -> RadsData:
    """
    Receives raw source data from extract_from().
    Partitions and computes statistics to be displayed by the app.
    This dept currently does not have any user parameters from sidebar.
    """
    # Create a copy of all income statements, then combine and normalize data in one table
    stmts = [stmt.copy() for stmt in raw.income_statements]
    stmt = _normalize_income_stmts(stmts)

    # Partition based on department
    df_by_dept = _partition_income_stmt(stmt)

    df = generate_income_stmt(df_by_dept[DEPT_CT], INCOME_STATEMENT_DEF)

    # # Group and sort data in income statments based on categories like revenue, expenses, etc
    # income_stmt_by_dept = {
    #     dept: _process_income_stmt(df) for dept, df in df_by_dept.items()
    # }

    stats = _calc_stats(raw)
    return RadsData(raw=raw, income_stmt_by_dept=None, stats=stats)


def _normalize_income_stmts(stmts: list[pd.DataFrame]):
    """
    Combine all income statments into one table:
     - Add the month to the data as a new column
     - Use the headers are stored in row 2
     - Normalize values in the column 1 (Cost Center) to a standard ID for the department
    """
    ret = []
    for df in stmts:
        # Extract the month and year from cell E1, which should read "Month to Date: MM/YYYY"
        month_year = df.iloc[0, 4].split(":")[1].strip()
        month, year = month_year.split("/")

        # Use row 2 as the column names and drop the first two rows
        df.columns = df.iloc[1]
        df = df.iloc[2:]

        # Normalize column names
        df.columns.values[4] = "Actual"
        df.columns.values[5] = "Budget"

        # Normalize values using our defined maps. fillna() is used to retain any unknown values not
        # specified in the dict.
        df["Cost Center"] = df["Cost Center"].map(DEPT_ID_MAP).fillna(df["Cost Center"])

        # Insert a new column for the month
        df.insert(0, "Month", f"{year}-{month}")
        ret.append(df)

    return pd.concat(ret)


def _partition_income_stmt(stmt: pd.DataFrame):
    """
    Receives a dataframe with the income statement data.
    Returns a new dict keyed on the unique values found in the "Cost Center" column across all the data in the form:
        { "Ledger Account": pd.DataFrame }
    """
    ret = {}

    # Iterate over the unique values in the "Cost Center" column
    for dept in stmt["Cost Center"].unique():
        # Filter and store the data based on the current department
        dept_data = stmt[stmt["Cost Center"] == dept]
        if dept in ret:
            ret[dept] = pd.concat([ret[dept], dept_data])
        else:
            ret[dept] = dept_data

    return ret


def aggrid_income_stmt(df):
    # Bold these Ledger Account rows
    bold_rows = [
        "Operating Revenues",
        "Total Revenue",
        "Net Revenue",
        "Expenses",
        "Total Operating Expenses",
        "Operating Margin",
        "Contribution Margin",
    ]

    # Create AgGrid display configuration to do row grouping and bolding
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_grid_options(
        # Auto-size columns, based width on content, not header
        skipHeaderOnAutoSize=True,
        suppressColumnVirtualisation=True,
        # Bold columns based on contents of the Legder Account column
        # getRowStyle=JsCode(
        #     f"""
        #     function(params) {{
        #         if ({ str(bold_rows) }.includes(params.data['Ledger Account'])) {{
        #             return {{'font-weight': 'bold'}}
        #         }}
        #     }}
        #     """
        # ),
        # Row grouping
        autoGroupColumnDef=dict(
            # Don't show a column name
            headerName="",
            maxWidth=90,
            # Don't add suffice with count of grouped up rows - eg. "> Supplies (10)"
            # And innerRenderer() returning null results in blank text for grouped rows
            cellRendererParams=dict(
                suppressCount=True, innerRenderer=JsCode("function() {}")
            ),
            # For grouped rows (those that have a hier value with a /), use the
            # default rendere agGroupCellRenderer, which will show the toggle button
            # and call innerRenderer to determine the text to show.
            #
            # For non-grouped rows, just return an empty <span> so no text is shown.
            cellRendererSelector=JsCode(
                """
                function(params) {
                    class EmptyRenderer {
                        getGui() { return document.createElement('span') }
                        refresh() { return true; }
                    }
                    if (params.value && !params.value.indexOf('/')) {
                        return null
                    } else {
                        return {
                            component: 'agGroupCellRenderer',
                        };
                    }
                }
                """,
            ),
        ),
        # Row grouping is actually using AgGrid Tree Data mode. See _hierarchy_from_row_groups() for
        # how the tree paths are generated.
        treeData=True,
        getDataPath=JsCode("function(data) { return data.hier.split('/'); }"),
        animateRows=True,
        # groupDefaultExpanded=-1,
    )
    # gb.configure_column("i", headerName="Row", valueGetter="node.rowIndex", pinned="left", width=30)
    gb.configure_column("hier", hide=True)

    # Configure decimals, commas, etc when displaying of money and percent columns
    gb.configure_columns(
        [
            "Actual",
            "Budget",
        ],
        type=["numericColumn", "numberColumnFilter", "customNumericFormat"],
        valueFormatter=JsCode(
            "function(params) { return (params.value == null) ? params.value : params.value.toLocaleString('en-US', { maximumFractionDigits:2 }) }"
        ),
    )

    # Finally show data table
    AgGrid(
        df,
        gridOptions=gb.build(),
        # columns_auto_size_mode=ColumnsAutoSizeMode.FIT_CONTENTS,
        allow_unsafe_jscode=True,
    )
    # Work around to ensure that AgGrid height doesn't collapse when in non-active tab after user interactions
    st.markdown(
        """
        <style>
            .element-container iframe {
                min-height: 810px;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def generate_income_stmt(df, statement_def):
    # Create new column that combines Spend and Revenue Categories
    df = df.copy()
    df["Category"] = df.apply(
        lambda row: row["Spend Category"]
        if row["Spend Category"] != "(Blank)"
        else row["Revenue Category"],
        axis=1,
    )

    ret = pd.DataFrame(columns=["hier", "Ledger Account", "Actual", "Budget"])

    def process_item(item, path):
        if "name" in item and "items" in item:
            cur_path = item["name"] if path == "" else f"{path}/{item['name']}"
            ret.loc[len(ret)] = [
                cur_path,
                item["name"],
                None,
                None,
            ]
            for sub_item in item["items"]:
                process_item(sub_item, cur_path)

        if "account" in item:
            account = item["account"]
            category = item.get("category")
            if category == "*":
                cur_path = f"{account}" if path == "" else f"{path}/{account}"

                ret.loc[len(ret)] = [cur_path, account, None, None]

                unique_categories = set(
                    df.loc[df["Ledger Account"] == account, "Category"].unique()
                )
                for cat in sorted(unique_categories):
                    process_item({"account": account, "category": cat}, cur_path)
            else:
                cur_path = f"{account}-{category}" if category else account
                cur_path = cur_path if path == "" else f"{path}/{cur_path}"
                mask = df["Ledger Account"] == account
                if category:
                    mask = mask & (df["Category"] == category)
                rows = df.loc[mask, ["Ledger Account", "Actual", "Budget"]]
                for _, row in rows.iterrows():
                    ret.loc[len(ret)] = [
                        cur_path,
                        category if category else row["Ledger Account"],
                        row["Actual"],
                        row["Budget"],
                    ]

        if "total" in item:
            cur_path = item["name"] if path == "" else f"{path}/{item['name']}"
            total_accounts = item["total"]
            actual = 0
            budget = 0
            for acct in total_accounts:
                actual += ret.loc[ret["hier"].str.startswith(acct), "Actual"].sum()
                budget += ret.loc[ret["hier"].str.startswith(acct), "Budget"].sum()
            ret.loc[len(ret)] = [cur_path, item["name"], actual, budget]

    for item in statement_def:
        process_item(item, "")

    aggrid_income_stmt(ret)
    st.write(ret)
    return ret


def _process_income_stmt(stmt: pd.DataFrame) -> IncomeStatement:
    revenue = pd.DataFrame(
        columns=[
            "Month",
            "Revenue Category",
            "Ledger Account",
            "Actual",
            "Budget",
            "Variance",
            "Variance %",
        ]
    )
    deductions = pd.DataFrame(
        columns=[
            "Month",
            "Ledger Account",
            "Actual",
            "Budget",
            "Variance",
            "Variance %",
        ]
    )
    expenses = pd.DataFrame(
        columns=[
            "Month",
            "Ledger Account",
            "Actual",
            "Budget",
            "Variance",
            "Variance %",
        ]
    )

    # Filter and sort each section - revenue, expenses, deductions
    df = stmt[stmt["Ledger Account"].isin(REVENUE_ACCOUNTS)]
    revenue = revenue.append(
        pd.DataFrame(df.iloc[:, [0, 4, 1, 5, 6, 7, 8]].values, columns=revenue.columns)
    )

    df = stmt[stmt["Ledger Account"].isin(DEDUCTION_ACCOUNTS)]
    deductions = deductions.append(
        pd.DataFrame(df.iloc[:, [0, 1, 5, 6, 7, 8]].values, columns=deductions.columns)
    )

    df = stmt[stmt["Ledger Account"].isin(EXPENSE_ACCOUNTS)]
    expenses = expenses.append(
        pd.DataFrame(df.iloc[:, [0, 1, 5, 6, 7, 8]].values, columns=expenses.columns)
    )

    return IncomeStatement(revenue, deductions, expenses)


def _calc_stats(raw: RawData) -> dict:
    """Precalculate statistics from raw data that will be displayed on dashboard"""
    s = {}
    return s
