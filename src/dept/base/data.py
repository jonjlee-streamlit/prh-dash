"""
Transform source data into department specific data that can be displayed on dashboard
"""

import pandas as pd
from dataclasses import dataclass
from datetime import date
from dateutil.relativedelta import relativedelta
from .configs import DeptConfig
from ... import source_data, income_statment, static_data


@dataclass(frozen=True)
class DeptData:
    # Settings
    dept: str
    month: str

    # Patient volumes from stats report card
    volumes: pd.DataFrame

    # Productive / Non-productive hours
    hours: pd.DataFrame

    # Summary table of hours and FTE
    hours_for_month: pd.DataFrame
    hours_ytm: pd.DataFrame

    # Income statement for a specific department and time period
    income_stmt: pd.DataFrame

    # Single value calculations, like YTD volume
    stats: dict


def process(
    config: DeptConfig, settings: dict, src: source_data.SourceData
) -> DeptData:
    """
    Receives raw source data from database.
    Partitions and computes statistics to be displayed by the app.
    settings contains any configuration from the sidebar that the user selects.
    """
    dept_id, month = (
        settings["dept_id"],
        settings["month"],
    )

    # Get department IDs that we will be matching
    if dept_id == "All":
        wd_ids = config.wd_ids
    else:
        wd_ids = [dept_id]

    # Sort volume data by time
    volumes_df = src.volumes_df[src.volumes_df["dept_wd_id"].isin(wd_ids)]
    volumes = _calc_volumes_history(volumes_df)
    latest_volume_month = volumes["month"].max()

    # Organize income statement data into a human readable table grouped into categories
    income_stmt_df = src.income_stmt_df[src.income_stmt_df["dept_wd_id"].isin(wd_ids)]

    # Create summary tables for hours worked by month and year
    hours_df = src.hours_df[src.hours_df["dept_wd_id"].isin(wd_ids)]
    hours_for_month = _calc_hours_for_month(hours_df, month)
    hours_ytm = _calc_hours_ytm(hours_df, month)
    hours_ytd = _calc_hours_ytm(hours_df, latest_volume_month)
    hours_df = _calc_hours_history(hours_df)

    # Pre-calculate statistics that are individual numbers, like overall revenue per encounter
    stats = _calc_stats(wd_ids, settings, src, volumes, hours_ytd, income_stmt_df)

    return DeptData(
        dept=wd_ids,
        month=month,
        volumes=volumes,
        hours=hours_df,
        hours_for_month=hours_for_month,
        hours_ytm=hours_ytm,
        income_stmt=income_stmt_df,
        stats=stats,
    )


def _calc_volumes_history(df: pd.DataFrame) -> pd.DataFrame:
    """
    Returns volumes for each month totaled across departments, sorted in reverse chronologic order by month
    """
    df = df.groupby("month")["volume"].sum().reset_index()
    return df.sort_values(by=["month"], ascending=[False])


def _calc_hours_for_month(df: pd.DataFrame, month: str) -> pd.DataFrame:
    """
    Given a month, summarize the regular, overtime, productive/non-productive hours and total FTE
    month should be in the format YYYY-MM
    """
    # Find the rows for the latest month
    df = df[df["month"] == month].reset_index(drop=True)

    # Return the columns that are displayed in the FTE tab summary table
    columns = [
        "reg_hrs",
        "overtime_hrs",
        "prod_hrs",
        "nonprod_hrs",
        "total_hrs",
        "total_fte",
    ]
    if df.shape[0] > 0:
        return df.loc[:, columns].sum()
    else:
        return pd.DataFrame(columns=columns)


def _calc_hours_ytm(df: pd.DataFrame, month: str) -> pd.DataFrame:
    """
    Return a dataframe with a single row containing the sum of the productive/non-productive hours across all departments for this year
    """
    # Filter all rows that are in the same year and come before the given month
    year = month[:4]
    df = df[df["month"].str.startswith(year) & (df["month"] <= month)]

    # Sum all rows. Return columns that are displayed in the FTE tab summary table.
    columns = [
        "reg_hrs",
        "overtime_hrs",
        "prod_hrs",
        "nonprod_hrs",
        "total_hrs",
        "total_fte",
    ]
    if df.shape[0] > 0:
        df = df[columns]
        return df.sum()
    else:
        return pd.DataFrame(columns=columns)


def _calc_hours_history(df: pd.DataFrame) -> pd.DataFrame:
    """
    Returns productive / non-productive hours and FTE for each month totaled across departments, sorted in reverse chronologic order by month
    """
    df = df.groupby("month").sum().reset_index()
    df = df.sort_values(by=["month"], ascending=[True])
    return df[
        [
            "month",
            "reg_hrs",
            "overtime_hrs",
            "prod_hrs",
            "nonprod_hrs",
            "total_hrs",
            "total_fte",
        ]
    ]


def calc_income_stmt_for_month(stmt: pd.DataFrame, month: str) -> pd.DataFrame:
    # Filter data for given month
    stmt = stmt[stmt["month"] == month]
    ret = income_statment.generate_income_stmt(stmt)
    return ret


def _calc_stats(
    wd_ids: list,
    settings: dict,
    src: source_data.SourceData,
    volumes: pd.DataFrame,  # volumes for each sub-department, all months
    hours_ytd: pd.DataFrame,  # one row with total hours for all sub-departments
    income_stmt_df: pd.DataFrame,  # all income statment data for sub-departments, all months
) -> dict:
    """Precalculate statistics from raw data that will be displayed on dashboard"""
    s = {}

    # Get the volume for the selected month and current year. The volumes table has
    # one number in the volume column for each department per month
    sel_month = settings["month"]
    sel_year = sel_month[:4]
    cur_year = str(date.today().year)
    month_volume = volumes.loc[volumes["month"] == sel_month, "volume"].sum()
    ytm_volume = volumes.loc[
        volumes["month"].str.startswith(sel_year) & (volumes["month"] <= sel_month),
        "volume",
    ].sum()
    ytd_volume = volumes.loc[volumes["month"].str.startswith(cur_year), "volume"].sum()

    # There is one budget row for each department. Sum them for overall budget,
    # and divide by the months in the year so far for the YTD volume and hours budgets.
    budget_df = src.budget_df[src.budget_df["dept_wd_id"].isin(wd_ids)]
    budget_df = budget_df[
        [
            "budget_fte",
            "budget_hrs",
            "budget_volume",
            "budget_hrs_per_volume",
            "hourly_rate",
        ]
    ].sum()

    # Hours data - table has one row per department with columns for types of hours,
    # eg. productive, non-productive, overtime, ...
    ytd_prod_hours = hours_ytd["prod_hrs"].sum()
    ytd_hours = hours_ytd["total_hrs"].sum()

    # Get YTD revenue / expense data from the latest available income statement.
    # The most straight-forward way to do this is to generate an actual income statement
    # because the income statement definition already defines all the line items to total
    # for revenue vs expenses.
    #
    # First, generate income statment for the latest month available in the data. The "month"
    # column is in the format "YYYY-MM".
    latest_income_stmt_df = income_stmt_df[
        income_stmt_df["month"] == income_stmt_df["month"].max()
    ]
    income_stmt_ytd = income_statment.generate_income_stmt(latest_income_stmt_df)
    # Pull the YTD Actual and YTD Budget totals for revenue and expenses
    # Those columns can change names, so index them as the second to last, or -2 column (YTD Actual),
    # and last, or -1 column (YTD Budget)
    df_revenue = income_stmt_ytd[income_stmt_ytd["hier"] == "Net Revenue"]
    df_expense = income_stmt_ytd[income_stmt_ytd["hier"] == "Total Operating Expenses"]
    ytd_revenue = df_revenue.iloc[0, -2]
    ytd_budget_revenue = df_revenue.iloc[0, -1]
    ytd_expense = df_expense.iloc[0, -2]
    ytd_budget_expense = df_expense.iloc[0, -1]

    # Get the YTD budgeted volume based on the proportion of the annual budgeted volume
    # for the number of months of the year for which we have revenue / income statement information
    [income_stmt_max_year, income_stmt_max_month] = (
        income_stmt_df["month"].max().split("-")
    )
    if income_stmt_max_year == cur_year:
        ytd_budget_volume = budget_df.at["budget_volume"] * (
            int(income_stmt_max_month) / 12
        )
    else:
        # No revenue data for current year yet, YTD budgets are all 0
        ytd_budget_volume = 0

    # Volumes for the selected month and YTD show up on the Volumes tab, Summary section
    s["month_volume"] = month_volume
    s["ytm_volume"] = ytm_volume
    s["ytd_volume"] = ytd_volume

    # Budgeted FTE shows up as a threshold line on the FTE graph
    s["budget_fte"] = budget_df.at["budget_fte"]

    # KPIs
    s["revenue_per_volume"] = ytd_revenue / ytd_volume if ytd_volume > 0 else 0
    s["expense_per_volume"] = ytd_expense / ytd_volume if ytd_volume > 0 else 0

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

    s["hours_per_volume"] = ytd_prod_hours / ytd_volume
    s["target_hours_per_volume"] = budget_df.at["budget_hrs_per_volume"]
    s["variance_hours_per_volume"] = (
        s["target_hours_per_volume"] - s["hours_per_volume"]
    )
    if ytd_hours:
        s["fte_variance"] = (s["variance_hours_per_volume"] * ytd_volume) / (
            static_data.FTE_HOURS_PER_YEAR * (ytd_prod_hours / ytd_hours)
        )
        s["fte_variance_dollars"] = (
            s["variance_hours_per_volume"] * ytd_volume * budget_df.at["hourly_rate"]
        )
    else:
        s["fte_variance"] = 0
        s["fte_variance_dollars"] = 0

    return s
