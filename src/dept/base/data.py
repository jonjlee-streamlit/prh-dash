"""
Transform source data into department specific data that can be displayed on dashboard
"""

import pandas as pd
from dataclasses import dataclass
from datetime import date
from .configs import DeptConfig
from ... import source_data, income_statment, static_data


@dataclass(frozen=True)
class DeptData:
    # Settings
    dept: str
    month: str
    pay_period: str

    # Patient volumes from stats report card
    volumes: pd.DataFrame

    # Productive / Non-productive hours
    hours: pd.DataFrame

    # Summary tables of hours and FTE
    hours_for_month: pd.DataFrame
    hours_ytd: pd.DataFrame

    # Income statement for a specific department and time period
    income_stmt: pd.DataFrame

    # Single value calculations, like YTD volume
    stats: dict


def process(config: DeptConfig, settings: dict, src: source_data.SourceData) -> DeptData:
    """
    Receives raw source data from database.
    Partitions and computes statistics to be displayed by the app.
    settings contains any configuration from the sidebar that the user selects.
    """
    dept_id, month, pay_period = (
        settings["dept_id"],
        settings["month"],
        settings.get("pay_period", "2023-01"),
    )

    # Get department IDs that we will be matching
    if dept_id == "All":
        wd_ids = config.wd_ids
    else:
        wd_ids = [dept_id]

    # Sort volume data by time
    volumes_df = src.volumes_df[src.volumes_df["dept_wd_id"].isin(wd_ids)]
    volumes = volumes_df.sort_values(by=["month", "dept_name"], ascending=[False, True])

    # Organize income statement data into a human readable table grouped into categories
    income_stmt_df = src.income_stmt_df[src.income_stmt_df["dept_wd_id"].isin(wd_ids)]
    income_stmt = _calc_income_stmt_for_month(income_stmt_df, month)

    # Create summary tables for hours worked by month and year
    hours_df = src.hours_df[src.hours_df["dept_wd_id"].isin(wd_ids)]
    hours_for_month = _calc_hours_for_payperiod(hours_df, pay_period)
    hours_ytd = _calc_hours_ytd(hours_df)

    # Pre-calculate statistics that are individual numbers, like overall revenue per encounter
    stats = _calc_stats(wd_ids, settings, src, volumes, hours_ytd, income_stmt_df)

    return DeptData(
        dept=wd_ids,
        month=month,
        pay_period=pay_period,
        volumes=volumes,
        hours=hours_df,
        hours_for_month=hours_for_month,
        hours_ytd=hours_ytd,
        income_stmt=income_stmt,
        stats=stats,
    )


def _calc_hours_for_payperiod(df: pd.DataFrame, pay_period: str) -> pd.DataFrame:
    """
    Given a pay period, summarize the regular, overtime, productive/non-productive hours and total FTE
    payperiod should be in the format YYYY-##, where ## is between 01 and 26
    """
    # Find the row that matches our pay period
    df = df[df["pay_period"] == pay_period].reset_index(drop=True)

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


def _calc_hours_ytd(df: pd.DataFrame) -> pd.DataFrame:
    """
    Return a dataframe with a single row containing the sum of the productive/non-productive hours across all departments for this year
    """
    # Filter all rows for the current year
    year = str(date.today().year)
    df = df[df["pay_period"].str.startswith(year)]

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


def _calc_income_stmt_for_month(stmt: pd.DataFrame, month: str) -> pd.DataFrame:
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
    sel_month, cur_year = settings["month"], str(date.today().year)
    month_volume = volumes.loc[volumes["month"] == sel_month, "volume"].sum()
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
    ytd_budget_df = budget_df * ((date.today().month - 1) / 12)
    ytd_budget_volume = ytd_budget_df.at["budget_volume"]
    hourly_rate = ytd_budget_df.at["hourly_rate"]

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

    # Volumes for the selected month and YTD show up on the Volumes tab, Summary section
    s["month_volume"] = month_volume
    s["ytd_volume"] = ytd_volume

    # Budgeted FTE shows up as a threshold line on the FTE graph
    s["budget_fte"] = budget_df.at["budget_fte"]

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
    s["target_hours_per_volume"] = budget_df.at["budget_hrs_per_volume"]
    s["variance_hours_per_volume"] = (
        s["target_hours_per_volume"] - s["hours_per_volume"]
    )
    if ytd_hours:
        s["fte_variance"] = (s["variance_hours_per_volume"] * ytd_volume) / (
            static_data.FTE_HOURS_PER_YEAR * (ytd_prod_hours / ytd_hours)
        )
        s["fte_variance_dollars"] = (
            s["variance_hours_per_volume"] * ytd_volume * hourly_rate
        )
    else:
        s["fte_variance"] = 0
        s["fte_variance_dollars"] = 0

    return s
