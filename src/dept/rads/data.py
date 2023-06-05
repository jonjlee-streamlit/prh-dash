import pandas as pd
from dataclasses import dataclass
from ...RawData import RawData
from ...income_statment import generate_income_stmt

# Dict used to normalize various identifiers for the same department
DEPT_MRI = "MRI"
DEPT_CT = "CT"
DEPT_XR = "XR"
DEPT_IMAGING_SERVICES = "SERVICES"
DEPT_ULTRASOUND = "US"
DEPT_MAMMOGRAPHY = "MAMMO"
DEPT_NUCLEAR = "NM"
DEPT_ID_MAP = {
    "CT Scan": DEPT_CT,
    "PRH CT SCAN": DEPT_CT,
    "CC_71300": DEPT_CT,
    "MRI": DEPT_MRI,
    "PRH MRI": DEPT_MRI,
    "CC_71200": DEPT_MRI,
    "Imaging Services": DEPT_IMAGING_SERVICES,
    "PRH IMAGING SERVICES": DEPT_IMAGING_SERVICES,
    "CC_71400": DEPT_IMAGING_SERVICES,
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


@dataclass
class RadsData:
    """Represents processed department specific data"""

    # Original data set
    raw: RawData

    # Income statement filtered by department
    income_stmt_by_dept: dict[str, pd.DataFrame]

    # Calculated statistics
    stats: dict


def process(raw: RawData) -> RadsData:
    """
    Receives raw source data from extract_from().
    Partitions and computes statistics to be displayed by the app.
    This dept currently does not have any user parameters from sidebar.
    """
    # Create a copy of all income statements, then combine and normalize data in one table
    if len(raw.income_statements) > 0:
        stmts = [stmt.copy() for stmt in raw.income_statements]
        stmt = _normalize_income_stmts(stmts)

        # Partition based on department
        df_by_dept = _partition_income_stmt(stmt)

        # Organize data items into an income statment
        income_stmt_by_dept = {}
        for dept, df in df_by_dept.items():
            income_stmt_by_dept[dept] = generate_income_stmt(df)

    else:
        income_stmt_by_dept = None

    # Pre-calculate statistics to display
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

        # Normalize column names
        df.columns.values[4] = "Actual"
        df.columns.values[5] = "Budget"

        # Normalize values using our defined maps. fillna() is used to retain any unknown values not
        # specified in the dict.
        df["Cost Center"] = df["Cost Center"].map(DEPT_ID_MAP).fillna(df["Cost Center"])

        # Insert a new column for the month
        df.insert(0, "Month", f"{year}-{month}")
        ret.append(df)

    return pd.concat(ret) if len(ret) > 0 else None


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


def _calc_stats(raw: RawData) -> dict:
    """Precalculate statistics from raw data that will be displayed on dashboard"""
    s = {}
    return s
