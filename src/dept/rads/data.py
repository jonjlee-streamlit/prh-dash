import pandas as pd
from dataclasses import dataclass
from ...RawData import RawData
from ...IncomeStatement import IncomeStatement

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

# Normal values for revenue categories
REVENUE_CATEGORY_MAP = {
    "Clinic Revenue": "Clinic",
    "Inpatient Revenue": "Inpatient",
    "Outpatient Revenue": "Outpatient",
    "(Blank)": ""
}
REVENUE_ACCOUNTS = ["40000:Patient Revenues", "40010:Sales Revenue", "40300:Other Operating Revenue"]
DEDUCTION_ACCOUNTS = ["49000:Contractual Adjustments", "49001:Bad Debts & Write Offs", "49002:Administrative Write Offs"]
EXPENSE_ACCOUNTS = ["50000:Salaries & Wages", "50011:Benefits-Taxes", "50012:Benefits-Insurance", "50013:Benefits-Retirement", "50014:Benefits-Other", "60220:Professional Fees", "60221:Temp Labor", "60222:Locum Tenens", "60300:Supplies", "60336:Pharmaceuticals", "60500:Utilities", "60600:Purchased Services", "60620:Maintenance", "60650:Software Licenses", "60800:Leases/Rents Operating", "60951:Professional Memberships", "60960:Other Direct Expenses", "60970:Travel & Education", "61003:Licensing Fees State", "70000:Depreciation"]

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

    # Group and sort data in income statments based on categories like revenue, expenses, etc
    income_stmt_by_dept = {dept: _process_income_stmt(df) for dept, df in df_by_dept.items()}

    stats = _calc_stats(raw)
    return RadsData(raw=raw, income_stmt_by_dept=income_stmt_by_dept, stats=stats)

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

        # Normalize values using our defined maps. fillna() is used to retain any unknown values not
        # specified in the dict.
        df["Cost Center"] = df["Cost Center"].map(DEPT_ID_MAP).fillna(df["Cost Center"])
        df["Revenue Category"] = df["Revenue Category"].map(REVENUE_CATEGORY_MAP).fillna(df["Revenue Category"])

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

def _process_income_stmt(stmt: pd.DataFrame) -> IncomeStatement:
    revenue = pd.DataFrame(columns=["Month", "Revenue Category", "Ledger Account", "Actual", "Budget", "Variance", "Variance %"])
    deductions = pd.DataFrame(columns=["Month", "Ledger Account", "Actual", "Budget", "Variance", "Variance %"])
    expenses = pd.DataFrame(columns=["Month", "Ledger Account", "Actual", "Budget", "Variance", "Variance %"])

    # Filter and sort each section - revenue, expenses, deductions
    df = stmt[stmt["Ledger Account"].isin(REVENUE_ACCOUNTS)]
    revenue = revenue.append(pd.DataFrame(df.iloc[:, [0,4,1,5,6,7,8]].values, columns=revenue.columns))

    df = stmt[stmt["Ledger Account"].isin(DEDUCTION_ACCOUNTS)]
    deductions = deductions.append(pd.DataFrame(df.iloc[:, [0,1,5,6,7,8]].values, columns=deductions.columns))

    df = stmt[stmt["Ledger Account"].isin(EXPENSE_ACCOUNTS)]
    expenses = expenses.append(pd.DataFrame(df.iloc[:, [0,1,5,6,7,8]].values, columns=expenses.columns))

    return IncomeStatement(revenue, deductions, expenses)

def _calc_stats(raw: RawData) -> dict:
    """Precalculate statistics from raw data that will be displayed on dashboard"""
    s = {}
    return s
