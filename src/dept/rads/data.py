import typing
import pandas as pd
import streamlit as st
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
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
    "XR": DEPT_XR,
    "CT": DEPT_CT,
    "CT Scan": DEPT_CT,
    "PRH CT SCAN": DEPT_CT,
    "CC_71300": DEPT_CT,
    "MRI": DEPT_MRI,
    "MRI": DEPT_MRI,
    "PRH MRI": DEPT_MRI,
    "CC_71200": DEPT_MRI,
    "Imaging Services": DEPT_IMAGING_SERVICES,
    "PRH IMAGING SERVICES": DEPT_IMAGING_SERVICES,
    "CC_71400": DEPT_IMAGING_SERVICES,
    "US": DEPT_ULTRASOUND,
    "Ultrasound": DEPT_ULTRASOUND,
    "PRH ULTRASOUND": DEPT_ULTRASOUND,
    "CC_71430": DEPT_ULTRASOUND,
    "MAMMO": DEPT_MAMMOGRAPHY,
    "Mammography": DEPT_MAMMOGRAPHY,
    "PRH MAMMOGRAPHY": DEPT_MAMMOGRAPHY,
    "CC_71450": DEPT_MAMMOGRAPHY,
    "NM/PET": DEPT_NUCLEAR,
    "Nuclear Medicine": DEPT_NUCLEAR,
    "PRH NUCLEAR MEDICINE": DEPT_NUCLEAR,
    "CC_71600": DEPT_NUCLEAR,
}


@dataclass(frozen=True)
class RadsData:
    """Represents processed department specific data"""

    # Original data set
    raw: RawData

    # Settings
    dept: str
    month: str

    # Income statement for a specific department and time period
    income_stmt: pd.DataFrame

    # Historical volumes from stats report card
    volumes: pd.DataFrame

    # Volumes calculated from billing

    # Calculated statistics
    stats: dict


def process(settings: dict, raw: RawData) -> RadsData:
    """
    Receives raw source data from extract_from().
    Partitions and computes statistics to be displayed by the app.
    This dept currently does not have any user parameters from sidebar.
    """
    dept, month = settings["dept"], settings["month"]
    income_stmt = None
    volumes = None
    volume = 0

    if len(raw.income_statements) > 0:
        # Combine and normalize all income statment data into one table
        stmt = _normalize_income_stmts(raw.income_statements)

        # Partition based on department
        df_by_dept = _partition_income_stmt(stmt)

        # Organize data items into an income statment
        if dept in df_by_dept:
            income_stmt = generate_income_stmt(df_by_dept[dept])

    if len(raw.rads_volumes) > 0:
        # Combine all historic volume data into one table
        dts = _month_str_to_dates(month)
        volumes = _normalize_volumes(raw.rads_volumes)

        # Filter out our department data and sort by time
        volumes = _filter_by_dept(volumes, settings["dept"])
        volumes = volumes.sort_values(by=volumes.columns[0], ascending=False)

    # Pre-calculate statistics to display
    stats = _calc_stats(settings, raw, volumes)

    return RadsData(
        dept=dept,
        month=month,
        raw=raw,
        income_stmt=income_stmt,
        volumes=volumes,
        stats=stats,
    )


def _normalize_income_stmts(stmts: list[pd.DataFrame]):
    """
    Combine all income statments into one table:
     - Add the month to the data as a new column
     - Use the headers are stored in row 2
     - Normalize values in the column 1 (Cost Center) to a standard ID for the department
    """
    ret = []
    for df in stmts:
        # Do not modify original data
        df = df.copy()

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


def _normalize_volumes(volumes: list[pd.DataFrame]):
    """
    Combine all historical volume data into one table
    """
    # Transpose tables so there is a column for each dept and a row per month
    # and combine into 1 table
    df = pd.concat([v.T for v in volumes])

    # Drop blank second column and rows where the date is "YTD"
    df = df.drop(df.columns[1], axis=1)
    df = df[df.iloc[:, 0] != "YTD"]

    # First row is column headers. Map the values to our specific dept IDs.
    columns = list(df.iloc[0].map({**DEPT_ID_MAP, "TOTAL": "TOTAL"}).fillna(""))
    columns[0] = "Month"
    df.columns = columns
    df = df.iloc[1:]

    # Convert first column to month/year only (currently includes the day of month)
    df["Month"] = pd.to_datetime(df["Month"]).dt.to_period("M").dt.to_timestamp()

    return df


def _month_str_to_dates(month_str: str) -> typing.Tuple[datetime, datetime]:
    """
    Convert a month string, such as "Jan 2023" to start and end datetime objects.
    Returns a tuple (first datetime, last datetime).
    """
    first_day = datetime.strptime(month_str, "%b %Y")
    last_day = first_day + relativedelta(day=31)
    last_day = last_day.replace(hour=23, minute=59, second=59, microsecond=999)
    return (first_day, last_day)


def _filter_by_dept(df: pd.DataFrame, dept: str) -> pd.DataFrame:
    # Retain month column and column with the ID of the desired deptartment.
    # The department names in the source data are changed to the canonical
    # department ID in _normalize_volumes().
    df = df.loc[:, ["Month", dept]]
    df.columns = ["Month", "Volume"]
    return df


def _calc_stats(settings: dict, raw: RawData, volumes: pd.DataFrame) -> dict:
    """Precalculate statistics from raw data that will be displayed on dashboard"""
    # Get the volume for the selected month by the user, which will be in the format "Jan 2023"
    month = settings["month"]
    df = volumes.loc[volumes["Month"] == pd.to_datetime(month)]
    volume = df.iloc[0, 1] if df.shape[0] > 0 else 0
    s = {
        # Volume for this month
        "volume": volume
    }
    return s
