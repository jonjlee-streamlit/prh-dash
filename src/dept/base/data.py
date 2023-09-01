"""
Transform source data into department specific data that can be displayed on dashboard
"""

import pandas as pd
from dataclasses import dataclass
from datetime import date
from .depts import DeptConfig
from ...source_data import SourceData
from ...income_statment import generate_income_stmt
from ...static_data import FTE_HOURS_PER_DAY, FTE_HOURS_PER_YEAR


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


def process(config: DeptConfig, settings: dict, src: SourceData) -> DeptData:
    """
    Receives raw source data from database.
    Partitions and computes statistics to be displayed by the app.
    settings contains any configuration from the sidebar that the user selects.
    """
    dept, month, pay_period = (
        settings["dept"],
        settings["month"],
        settings["pay_period"],
    )

    # Get department IDs that we will be matching
    if dept == "ALL":
        wd_ids = config.wd_ids
    else:
        wd_ids = [dept]

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

    return DeptData(
        dept=wd_ids,
        month=month,
        pay_period=pay_period,
        volumes=volumes,
        hours=hours_df,
        hours_for_month=hours_for_month,
        hours_ytd=hours_ytd,
        income_stmt=income_stmt,
        stats={},
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
    ret = generate_income_stmt(stmt)
    return ret
