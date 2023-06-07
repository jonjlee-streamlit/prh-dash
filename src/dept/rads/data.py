import typing
import calendar
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
    "TOTAL": "TOTAL",
}

# Ratio to convert hours into FTE equivalent
FTE_HOURS_PER_YEAR = 2080
FTE_HOURS_PER_DAY = FTE_HOURS_PER_YEAR / 365


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
    income_stmt_ytd: pd.DataFrame

    # Historical volumes from stats report card
    volumes: pd.DataFrame

    # Volumes calculated from billing

    # Productive / Non-productive hours. Separate member for hours for this month and YTD
    hours: pd.DataFrame
    hours_for_month: pd.DataFrame
    hours_ytd: pd.DataFrame

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
    income_stmt_ytd = None
    volumes = None
    hours = None
    hours_for_month = None
    hours_ytd = None

    if len(raw.income_statements) > 0:
        # Combine and normalize all income statment data into one table
        income_stmts = _normalize_income_stmts(raw.income_statements)

        # Partition based on department
        stmt_by_dept = _partition_income_stmt(income_stmts)

        # Organize data items into an income statment
        if dept in stmt_by_dept:
            stmt = stmt_by_dept[dept]
            income_stmt = _calc_income_stmt_for_month(stmt, month)
            income_stmt_ytd = _calc_income_stmt_ytd(stmt)

    if len(raw.rads_volumes) > 0:
        # Combine all historic volume data into one table
        volumes = _normalize_volumes(raw.rads_volumes)

        # Filter out our department data and sort by time
        volumes = _filter_volumes_by_dept(volumes, dept)
        volumes = volumes.sort_values(by=volumes.columns[0], ascending=False)

    if len(raw.hours_by_month) > 0:
        # Combine and normalize all hours data into one table
        hours = _normalize_hours(raw.hours_by_month)
        # Filter data for our department and selected month
        hours = hours[hours["dept"] == dept]
        hours_for_month = _calc_hours_for_month(hours, month)
        hours_ytd = _calc_hours_ytd(hours)

    # Pre-calculate statistics to display
    stats = _calc_stats(settings, raw, income_stmt_ytd, volumes, hours_ytd)

    return RadsData(
        dept=dept,
        month=month,
        raw=raw,
        income_stmt=income_stmt,
        income_stmt_ytd=income_stmt_ytd,
        volumes=volumes,
        hours=hours,
        hours_for_month=hours_for_month,
        hours_ytd=hours_ytd,
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

        # Use row 2 as the column names and drop the first two rows
        df.columns = df.iloc[1]
        df = df.iloc[2:]

        # Normalize column names
        df.columns.values[4] = "Actual"
        df.columns.values[5] = "Budget"
        df.columns.values[11] = "Actual YTD"
        df.columns.values[12] = "Budget YTD"

        # Normalize values using our defined maps. fillna() is used to retain any unknown values not
        # specified in the dict.
        df["Cost Center"] = df["Cost Center"].map(DEPT_ID_MAP).fillna(df["Cost Center"])

        # Insert a new column for the month
        df.insert(0, "Month", pd.to_datetime(month_year))
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


def _calc_income_stmt_for_month(stmt: pd.DataFrame, month: str) -> pd.DataFrame:
    # Filter data for given month
    stmt = stmt[stmt["Month"] == month]
    ret = generate_income_stmt(stmt)
    return ret


def _calc_income_stmt_ytd(stmt: pd.DataFrame) -> pd.DataFrame:
    # Filter data for most recent month present
    month = stmt["Month"].max()
    stmt = stmt[stmt["Month"] == month]

    # Copy data from YTD data (columns L:M) to Actual and Budget columns (E:F)
    stmt = stmt.copy()
    stmt[["Actual", "Budget"]] = stmt[["Actual YTD", "Budget YTD"]]
    ret = generate_income_stmt(stmt)
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
    columns = list(df.iloc[0].map(DEPT_ID_MAP).fillna(""))
    columns[0] = "Month"
    df.columns = columns
    df = df.iloc[1:]

    # Convert first column to month/year only (currently includes the day of month)
    df["Month"] = pd.to_datetime(df["Month"]).dt.to_period("M").dt.to_timestamp()

    return df


def _filter_volumes_by_dept(df: pd.DataFrame, dept: str) -> pd.DataFrame:
    # Retain month column and column with the ID of the desired deptartment.
    # The department names in the source data are changed to the canonical
    # department ID in _normalize_volumes().
    df = df.loc[:, ["Month", dept]]
    df.columns = ["Month", "Volume"]
    return df


def _calc_volumes_ytd(df: pd.DataFrame) -> int:
    today = date.today()
    first_day = date(today.year, 1, 1)
    df = df[
        (df["Month"] >= pd.to_datetime(first_day))
        & (df["Month"] <= pd.to_datetime(today))
    ]
    return df["Volume"].fillna(0).sum(numeric_only=True)


def _normalize_hours(hours: list[pd.DataFrame]):
    """
    Combine separate hours tables into a single dataframe.
    Transform departments to canonical IDs, sum various categories of overtime and leave into single columns
    """
    ret = []
    for hours_df in hours:
        df = pd.DataFrame(
            columns=[
                "dept",
                "month",
                "regular",
                "overtime",
                "pct_overtime",
                "productive",
                "nonproductive",
                "pct_nonproductive",
                "total",
                "fte",
            ]
        )
        # Get the month from top left cell
        month = hours_df.iloc[0, 0]
        # Drop first and last two rows - headers and totals
        hours_df = hours_df[2:-2]
        # Ignore column 1, dept number. Remap column 2, dept name to canonical dept ID
        df["dept"] = hours_df.iloc[:, 1].map(DEPT_ID_MAP)
        # Add month to every row
        df["month"] = month
        # Copy column 3
        df["regular"] = hours_df.iloc[:, 2]
        # Sum columns 4-6 as overtime
        df["overtime"] = hours_df.iloc[:, 3:6].sum(axis=1)
        # Sum columns regular + overtime + education (columns 3-7) as productive hours
        df["productive"] = hours_df.iloc[:, 2:7].sum(axis=1)
        # Sum columns 9-16 as non-productive hours
        df["nonproductive"] = hours_df.iloc[:, 8:16].sum(axis=1)
        # Calculate % overtime, % non-productive, total hours, and FTE equivalient
        df["pct_overtime"] = df["overtime"] / (df["overtime"] + df["regular"])
        df["total"] = df["productive"] + df["nonproductive"]
        df["pct_nonproductive"] = df["nonproductive"] / (df["total"])
        df["fte"] = df["total"] / (
            FTE_HOURS_PER_DAY * calendar.monthrange(month.year, month.month)[1]
        )
        ret.append(df)

    return pd.concat(ret)


def _calc_hours_for_month(hours: pd.DataFrame, month) -> pd.DataFrame:
    data = [month, 0, 0, 0, 0, 0, 0]
    hours = hours[hours["month"] == month].reset_index(drop=True)
    if hours.shape[0] > 0:
        data = [
            month,
            hours.loc[0, "regular"],
            hours.loc[0, "overtime"],
            hours.loc[0, "productive"],
            hours.loc[0, "nonproductive"],
            hours.loc[0, "total"],
            hours.loc[0, "fte"],
        ]

    ret = pd.DataFrame(
        [data] if data else None,
        columns=[
            "",
            "Regular Hours",
            "OT Hours",
            "Productive Hours",
            "Non-productive Hours",
            "Total Paid Hours",
            "FTE",
        ],
    )

    return ret


def _calc_hours_ytd(hours: pd.DataFrame) -> pd.DataFrame:
    today = date.today()
    first_day = date(today.year, 1, 1)
    num_days = (today - first_day).days
    hours = hours[
        (hours["month"] >= pd.to_datetime(first_day))
        & (hours["month"] <= pd.to_datetime(today))
    ]
    data = None
    if hours.shape[0] > 0:
        data = [
            "YTD",
            hours["regular"].sum(),
            hours["overtime"].sum(),
            hours["productive"].sum(),
            hours["nonproductive"].sum(),
            hours["total"].sum(),
            hours["total"].sum() / (FTE_HOURS_PER_DAY * num_days),
        ]

    ret = pd.DataFrame(
        [data] if data else None,
        columns=[
            "",
            "Regular Hours",
            "OT Hours",
            "Productive Hours",
            "Non-productive Hours",
            "Total Paid Hours",
            "FTE",
        ],
    )

    return ret


def _calc_stats(
    settings: dict,
    raw: RawData,
    income_stmt_ytd: pd.DataFrame,
    volumes: pd.DataFrame,
    hours_ytd: pd.DataFrame,
) -> dict:
    """Precalculate statistics from raw data that will be displayed on dashboard"""
    # Income statement totals
    ytd_revenue, ytd_budget_revenue = 0, 0
    ytd_expense, ytd_budget_expense = 0, 0
    if income_stmt_ytd is not None and income_stmt_ytd.shape[0]:
        df = income_stmt_ytd[income_stmt_ytd["hier"] == "Net Revenue"]
        if df.shape[0]:
            ytd_revenue = df["Actual"].iloc[0]
            ytd_budget_revenue = df["Budget"].iloc[0]

        df = income_stmt_ytd[income_stmt_ytd["hier"] == "Total Operating Expenses"]
        if df.shape[0]:
            ytd_expense = df["Actual"].iloc[0]
            ytd_budget_expense = df["Actual"].iloc[0]

    # Get the volume for the selected month by the user, which will be in the format "Jan 2023"
    month = pd.to_datetime(settings["month"])
    df = volumes.loc[volumes["Month"] == month]
    month_volume = df.iloc[0, 1] if df.shape[0] > 0 else 0
    ytd_volume = _calc_volumes_ytd(volumes)

    # Hardcoded budgeted volumes - no source data available yet
    budget_volumes = {
        DEPT_MRI: 3750,
        DEPT_CT: 6000,
        DEPT_XR: 16700,
        DEPT_ULTRASOUND: 6400,
        DEPT_MAMMOGRAPHY: 3250,
        DEPT_NUCLEAR: 1350,
    }
    ytd_budget_volume = budget_volumes.get(settings["dept"], 0) * (
        date.today().month / 12
    )

    # Hours data
    ytd_prod_hours = 0
    ytd_hours = 0
    if hours_ytd is not None and hours_ytd.shape[0]:
        ytd_prod_hours = hours_ytd["Productive Hours"].iloc[0]
        ytd_hours = hours_ytd["Total Paid Hours"].iloc[0]

    # Hardcoded budgeted hours - no source data available yet
    budget_hours_per_volume_by_dept = {
        DEPT_MRI: 2.47,
        DEPT_CT: 0.30,
        DEPT_XR: 1.53,
        DEPT_ULTRASOUND: 1.62,
        DEPT_MAMMOGRAPHY: 1.35,
        DEPT_NUCLEAR: 2.53,
    }
    budget_fte_by_dept = {
        DEPT_MRI: 5.5,
        DEPT_CT: 1.0,
        DEPT_XR: 14.0,
        DEPT_ULTRASOUND: 5.9,
        DEPT_MAMMOGRAPHY: 2.6,
        DEPT_NUCLEAR: 2.0,
    }
    budget_hours_per_volume = budget_hours_per_volume_by_dept.get(settings["dept"], 0)
    budget_fte = budget_fte_by_dept.get(settings["dept"], 0)

    s = {
        "month_volume": 0 if pd.isna(month_volume) else month_volume,
        "ytd_volume": ytd_volume,
        "budget_fte": budget_fte,
    }

    # KPIs
    s["revenue_per_volume"] = ytd_revenue / ytd_volume
    s["expense_per_volume"] = ytd_expense / ytd_volume

    if ytd_budget_volume and ytd_budget_revenue and ytd_budget_expense:
        s["target_revenue_per_volume"] = ytd_budget_revenue / ytd_budget_volume
        s["variance_revenue_per_volume"] = round(
            (s["revenue_per_volume"] / s["target_revenue_per_volume"] - 1) * 100
        )
        s["target_expense_per_volume"] = ytd_budget_expense / ytd_budget_volume
        s["variance_expense_per_volume"] = round(
            (s["expense_per_volume"] / s["target_expense_per_volume"] - 1) * 100
        )
    else:
        s["target_revenue_per_volume"] = 0
        s["variance_revenue_per_volume"] = 0
        s["target_expense_per_volume"] = 0
        s["variance_expense_per_volume"] = 0

    s["hours_per_volume"] = ytd_hours / ytd_volume
    s["target_hours_per_volume"] = budget_hours_per_volume
    s["variance_hours_per_volume"] = (
        s["target_hours_per_volume"] - s["hours_per_volume"]
    )
    if ytd_hours:
        s["fte_variance"] = (s["variance_hours_per_volume"] * ytd_volume) / (
            FTE_HOURS_PER_YEAR * (ytd_prod_hours / ytd_hours)
        )
        s["fte_variance_dollars"] = (s["variance_hours_per_volume"] * ytd_volume) * (
            37.06  # Average hourly rate - currently hardcoded
        )
    else:
        s["fte_variance"] = 0
        s["fte_variance_dollars"] = 0

    return s
