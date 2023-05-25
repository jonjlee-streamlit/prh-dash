import pandas as pd
from dataclasses import dataclass
from ...RawData import RawData

# Dict used to normalize various identifiers for the same department
DEPT_ID_MAP = {
    "CT Scan": "CT",
    "PRH CT SCAN": "CT",
    "CC_71300": "CT",
    "MRI": "MRI",
    "PRH MRI": "MRI",
    "CC_71200": "MRI",
    "Imaging Services": "SERVICES",
    "PRH IMAGING SERVICES": "SERVICES",
    "CC_71400": "SERVICES",
    "Ultrasound": "ULTRASOUND",
    "PRH ULTRASOUND": "ULTRASOUND",
    "CC_71430": "ULTRASOUND",
    "Mammography": "MAMMOGRAPHY",
    "PRH MAMMOGRAPHY": "MAMMOGRAPHY",
    "CC_71450": "MAMMOGRAPHY",
    "Nuclear Medicine": "NUCLEAR",
    "PRH NUCLEAR MEDICINE": "NUCLEAR",
    "CC_71600": "NUCLEAR",
}

@dataclass
class RadsData:
    """Represents processed department specific data"""

    # Original data set
    raw: RawData

    # Income statement filtered by department
    income_stmt_by_dept: dict[pd.DataFrame]

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
    income_stmt_by_dept = _partition_income_stmt(stmt)

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

        # Use row 2 as the column names and drop the first two rows
        df.columns = df.iloc[1]
        df = df.iloc[2:]

        # Map values using the global dict. fillna() is used to retain any unknown values not
        # specified in the dict.
        df["Cost Center"] = df["Cost Center"].map(DEPT_ID_MAP).fillna(df["Cost Center"])

        # Insert a new column for the month
        df.insert(0, "Month", month_year)
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

def _calc_stats(raw: RawData) -> dict:
    """Precalculate statistics from raw data that will be displayed on dashboard"""
    s = {}
    return s
