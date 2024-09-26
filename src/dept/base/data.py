"""
Transform source data into department specific data that can be displayed on dashboard
"""

import pandas as pd
import math
from dataclasses import dataclass
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from .configs import DeptConfig
from ... import source_data, income_statment, static_data
from ... import util


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
    wd_ids = _get_all_wd_ids(config if dept_id == "All" else dept_id)

    # Group volume data by department and month
    volumes_df = src.volumes_df[src.volumes_df["dept_wd_id"].isin(wd_ids)]
    volumes = _calc_volumes_history(volumes_df)

    # Group UOS data by department and month
    uos_df = src.uos_df[src.uos_df["dept_wd_id"].isin(wd_ids)]
    uos = _calc_volumes_history(uos_df)

    # Organize income statement data into a human readable table grouped into categories
    income_stmt_df = src.income_stmt_df[src.income_stmt_df["dept_wd_id"].isin(wd_ids)]
    income_stmt = _calc_income_stmt_for_month(income_stmt_df, month)

    # Create summary tables for hours worked by month and year
    hours_df = src.hours_df[src.hours_df["dept_wd_id"].isin(wd_ids)]
    hours = _calc_hours_history(hours_df)
    hours_for_month = _calc_hours_for_month(hours_df, month)
    hours_ytm = _calc_hours_ytm(hours_df, month)

    # Summary table for contracted hours
    contracted_hours_df = src.contracted_hours_df[
        src.contracted_hours_df["dept_wd_id"].isin(wd_ids)
    ]

    # Pre-calculate statistics that are individual numbers, like overall revenue per encounter
    stats = _calc_stats(
        wd_ids,
        settings,
        src,
        volumes,
        uos,
        income_stmt_df,
        hours_df,
        contracted_hours_df,
    )

    return DeptData(
        dept=wd_ids,
        month=month,
        volumes=volumes,
        hours=hours,
        hours_for_month=hours_for_month,
        hours_ytm=hours_ytm,
        income_stmt=income_stmt,
        stats=stats,
    )


def _get_all_wd_ids(id_list):
    """Recursively find all ID strings in a mixed list of IDs and DeptConfig objects"""
    if isinstance(id_list, str):
        # ID is just one string, return it as single element in list
        return [id_list]
    elif isinstance(id_list, DeptConfig):
        return _get_all_wd_ids(id_list.wd_ids)
    else:
        # Return all strings in wd_ids and recurse into any embedded DeptConfigs
        ret = []
        for id in id_list:
            if isinstance(id, DeptConfig):
                ret += _get_all_wd_ids(id.wd_ids)
            else:
                ret.append(id)
        return ret


def _calc_volumes_history(df: pd.DataFrame) -> pd.DataFrame:
    """
    Returns volumes for each month totaled across all departments in data set, sorted in reverse chronologic order by month
    """
    # Group rows by month. Sum the volume and keep the first value for unit.
    df = (
        df.groupby("month")
        .agg(
            volume=("volume", "sum"),
            unit=("unit", "first"),
        )
        .reset_index()
    )
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
    [year_num, month_num] = month.split("-")
    df = df[df["month"].str.startswith(year_num) & (df["month"] <= month)]

    # Sum all rows, except FTE. Return columns that are displayed in the FTE tab summary table.
    # FTE needs to be recalculated based on the month number in the year.
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
        ret = df.sum()

        # For January, just use data in FTE column. Do not recalculate total_fte using hours. Use calculation for
        # subsequent months.
        month_num = int(month_num)
        if month_num > 1:
            ret["total_fte"] = ret["total_hrs"] / (
                util.fte_hrs_in_year(int(year_num)) * util.pct_of_year_through_date(month)
            )
        return ret
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
            "prod_hrs",
            "nonprod_hrs",
            "total_hrs",
            "total_fte",
        ]
    ]


def _calc_contracted_hours(df: pd.DataFrame) -> pd.DataFrame:
    """
    Returns contracted hours for this year YTD (up to given last updated month, which is in spreadsheet)
    """
    return df


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
    uos: pd.DataFrame,  # Unit of service (UOS) for each sub-department, all months
    income_stmt_df: pd.DataFrame,  # all income statment data for sub-departments, all months
    hours: pd.DataFrame,  # prod/non-prod hours and FTE for each sub-department
    contracted_hours_df: pd.DataFrame,  # traveler hours, currently pulled from manual entries in spreadsheet
) -> dict:
    """Precalculate statistics from raw data that will be displayed on dashboard"""
    s = {}

    # Get the currently selected month and year from the left sidebar, and its corresponding month from the last year
    sel_month = settings["month"]
    sel_year, month_of_sel_month = util.split_YYYY_MM(sel_month)
    prior_year = sel_year - 1
    month_in_prior_year = f"{prior_year:04d}-{month_of_sel_month:02d}"

    # Get the latest month that we will display depending on volume and income statement data available
    month_max, month_max_year, month_max_month = _max_month_to_display(
        volumes, uos, income_stmt_df
    )

    # Initialize all volume and uos stats to zero
    kpi_ytd_volume = 0
    month_volume, ytm_volume = 0, 0
    month_uos, ytm_uos, month_uos_in_prior_year, ytm_uos_in_prior_year = 0, 0, 0, 0
    uos_unit, volume_unit = "undefined", "undefined"

    # If UOS data is available, use it for KPIs. Otherwise, use volume data.
    kpi_uos_df = volumes if uos.empty else uos

    # Get the volume and UOS for the selected month / year. These tables have
    # one number in the volume column for each department per month
    if not volumes.empty:
        month_volume = volumes.loc[volumes["month"] == sel_month, "volume"].sum()
        ytm_volume = volumes.loc[
            volumes["month"].str.startswith(str(sel_year))
            & (volumes["month"] <= sel_month),
            "volume",
        ].sum()
        volume_unit = volumes.at[0, "unit"]
    if not uos.empty:
        month_uos = uos.loc[uos["month"] == sel_month, "volume"].sum()
        month_uos_in_prior_year = uos.loc[
            uos["month"] == month_in_prior_year, "volume"
        ].sum()
        ytm_uos_in_prior_year = uos.loc[
            uos["month"].str.startswith(str(prior_year))& (uos["month"] <= month_in_prior_year), "volume"
        ].sum()
        ytm_uos = uos.loc[
            uos["month"].str.startswith(str(sel_year)) & (uos["month"] <= sel_month),
            "volume",
        ].sum()
        uos_unit = uos.at[0, "unit"]

    # Get the denominator for KPI calculations - either YTD volume or UOS
    if not kpi_uos_df.empty:
        kpi_ytd_volume = kpi_uos_df.loc[
            kpi_uos_df["month"].str.startswith(str(month_max_year))
            & (kpi_uos_df["month"] <= month_max),
            "volume",
        ].sum()

    # There is one budget row for each department. Sum them for overall budget,
    # and divide by the months in the year so far for the YTD volume and hours budgets.
    budget_df = src.budget_df[src.budget_df["dept_wd_id"].isin(wd_ids)]
    budget_df = budget_df[
        [
            "budget_fte",
            "budget_prod_hrs",
            "budget_volume",
            "budget_uos",
            "budget_prod_hrs_per_uos",
            "hourly_rate",
        ]
    ].sum()
    # If there is more than one department, recalculate values that cannot just be summed across depts
    if len(wd_ids) > 1:
        # Prefer using UOS data to volume. If no data available, zero out the budgeted hrs per UOS
        if budget_df["budget_uos"] > 0:
            budget_df["budget_prod_hrs_per_uos"] = (
                budget_df["budget_prod_hrs"] / budget_df["budget_uos"]
            )
        elif uos.empty and budget_df["budget_volume"] > 0:
            budget_df["budget_prod_hrs_per_uos"] = (
                budget_df["budget_prod_hrs"] / budget_df["budget_volume"]
            )
        else:
            budget_df["budget_prod_hrs_per_uos"] = 0

        # Calculate average of hourly rates - this is not entirely accurate, since pay/hours are not distributed
        # evenly across departments. When possible, this will be recalulated below using (YTD salary / YTD hours)
        budget_df["hourly_rate"] = budget_df["hourly_rate"] / len(wd_ids)

    # Get the YTD budgeted volume based on the proportion of the annual budgeted volume
    # for the number of months of the year for which we have revenue / income statement information
    # Prefer UOS data if available, otherwise use volume
    budget_volume_for_kpi = (
        budget_df.at["budget_uos"] if not uos.empty else budget_df.at["budget_volume"]
    )
    ytd_budget_volume_for_kpi = budget_volume_for_kpi * (int(month_max_month) / 12)

    # Contracted hours data. This is separate from the hours data in the hours dataframe, which represents employee-only hours.
    # This table has has one row per department per year.
    year_for_contracted_hours = date.today().year
    month_num_for_contracted_hours = datetime.strptime(src.contracted_hours_updated_month[:10], "%Y-%m-%d").month
    month_for_contracted_hours = f"{year_for_contracted_hours:4d}-{month_num_for_contracted_hours:02d}"

    prior_year_for_contracted_hours = year_for_contracted_hours - 1
    contracted_hours_this_year_df = contracted_hours_df.loc[
        contracted_hours_df["year"] == year_for_contracted_hours,
        ["hrs"],
    ].sum()
    contracted_hours_prior_year_df = contracted_hours_df.loc[
        contracted_hours_df["year"] == prior_year_for_contracted_hours,
        ["hrs"],
    ].sum()
    contracted_fte_this_year = contracted_hours_this_year_df["hrs"] / (util.fte_hrs_in_year(year_for_contracted_hours) * util.pct_of_year_through_date(month_for_contracted_hours))
    contracted_fte_prior_year = contracted_hours_prior_year_df["hrs"] / util.fte_hrs_in_year(prior_year_for_contracted_hours)

    # Hours data - table has one row per department with columns for types of hours,
    # eg. productive, non-productive, overtime, ...
    hours_ytd = _calc_hours_ytm(hours, month_max)
    ytd_prod_hours = hours_ytd["prod_hrs"].sum() + contracted_hours_this_year_df["hrs"]
    ytd_hours = hours_ytd["total_hrs"].sum() + contracted_hours_this_year_df["hrs"]

    # Get YTD revenue, expense, and salary data from the income statement for month_max, where we have volume data.
    # The most straight-forward way to do this is to generate an actual income statement
    # because the income statement definition already defines all the line items to total
    # for revenue vs expenses.
    #
    # First, generate income statment for the latest month available in the data. The "month"
    # column is in the format "YYYY-MM".
    latest_income_stmt_df = income_stmt_df[income_stmt_df["month"] == month_max]
    income_stmt_ytd = income_statment.generate_income_stmt(latest_income_stmt_df)
    # Pull the YTD Actual and YTD Budget totals for revenue and expenses
    # Those columns can change names, so index them as the second to last, or -2 column (YTD Actual),
    # and last, or -1 column (YTD Budget)
    df_revenue = income_stmt_ytd[
        income_stmt_ytd["hier"].str.startswith("Operating Revenues|Patient Revenues")
        | income_stmt_ytd["hier"].str.startswith("Operating Revenues|Other")
    ].sum()
    df_expense = income_stmt_ytd[income_stmt_ytd["hier"] == "Total Operating Expenses"]
    # Salaries are for employees, Locum Tenens + Temp Labor are totals for contracted hours
    df_salary = income_stmt_ytd[
        income_stmt_ytd["hier"].str.startswith("Expenses|Salaries")
        | income_stmt_ytd["hier"].str.startswith(
            "Expenses|Professional Fees|60221:Temp Labor"
        )
        | income_stmt_ytd["hier"].str.startswith(
            "Expenses|Professional Fees|60222:Locum Tenens"
        )
    ].sum()
    ytd_revenue = df_revenue.iloc[-2]
    ytd_budget_revenue = df_revenue.iloc[-1]
    ytd_expense = df_expense.iloc[0, -2]
    ytd_budget_expense = df_expense.iloc[0, -1]
    ytd_salary = df_salary.iloc[-2]

    # Unit definitions for UOS and volumes
    s["uos_unit"] = uos_unit
    s["volume_unit"] = volume_unit

    # Dates used to calculate stats
    s["kpi_month_max"] = month_max
    s["month_in_prior_year"] = month_in_prior_year

    # Volumes and budgets for the selected month and YTD show up on the Volumes tab, Summary section
    s["month_volume"] = month_volume
    s["ytm_volume"] = ytm_volume
    s["month_budget_volume"] = budget_df.at["budget_volume"] / 12
    s["ytm_budget_volume"] = budget_df.at["budget_volume"] * (month_of_sel_month / 12)
    s["month_uos"] = month_uos
    s["ytm_uos"] = ytm_uos
    s["prior_year_month_uos"] = month_uos_in_prior_year
    s["prior_year_ytm_uos"] = ytm_uos_in_prior_year

    # Budgeted FTE shows up as a threshold line on the FTE graph
    s["budget_fte"] = budget_df.at["budget_fte"]

    # KPIs
    s["revenue_per_volume"] = ytd_revenue / kpi_ytd_volume if kpi_ytd_volume > 0 else 0
    s["expense_per_volume"] = ytd_expense / kpi_ytd_volume if kpi_ytd_volume > 0 else 0

    if ytd_budget_volume_for_kpi and ytd_budget_revenue and ytd_budget_expense:
        s["target_revenue_per_volume"] = ytd_budget_revenue / ytd_budget_volume_for_kpi
        s["variance_revenue_per_volume"] = math.trunc(
            (s["revenue_per_volume"] / s["target_revenue_per_volume"] - 1) * 100
        )
        s["target_expense_per_volume"] = ytd_budget_expense / ytd_budget_volume_for_kpi
        s["variance_expense_per_volume"] = math.trunc(
            (s["expense_per_volume"] / s["target_expense_per_volume"] - 1) * 100
        )
    else:
        s["target_revenue_per_volume"] = 0
        s["variance_revenue_per_volume"] = 0
        s["target_expense_per_volume"] = 0
        s["variance_expense_per_volume"] = 0

    s["hours_per_volume"] = ytd_prod_hours / kpi_ytd_volume if kpi_ytd_volume > 0 else 0
    s["target_hours_per_volume"] = budget_df.at["budget_prod_hrs_per_uos"]
    s["variance_hours_per_volume"] = (
        s["target_hours_per_volume"] - s["hours_per_volume"]
    )
    s["variance_hours_per_volume_pct"] = (
        math.trunc(-s["variance_hours_per_volume"] / s["target_hours_per_volume"] * 100)
        if s["target_hours_per_volume"] > 0
        else 0
    )
    if ytd_hours:
        # prefer to calculate hourly rate directly vs using data from Dashboard Supporting Data
        s["hourly_rate"] = ytd_salary / ytd_hours
        s["fte_variance"] = (s["variance_hours_per_volume"] * kpi_ytd_volume) / (
            static_data.FTE_HOURS_PER_YEAR * (ytd_prod_hours / ytd_hours)
        )
        s["fte_variance_dollars"] = (
            s["variance_hours_per_volume"] * kpi_ytd_volume * s["hourly_rate"]
        )
    else:
        s["fte_variance"] = 0
        s["fte_variance_dollars"] = 0

    # Contracted hours. This data is manually entered in the data spreadsheet currently, so we just
    # provide the specific data points for last year and this year
    s["contracted_hours_month"] = util.YYYY_MM_to_month_str(month_for_contracted_hours)
    s["contracted_hours"] = contracted_hours_this_year_df["hrs"]
    s["contracted_fte"] = contracted_fte_this_year
    s["prior_year_for_contracted_hours"] = str(prior_year_for_contracted_hours)
    s["prior_year_contracted_hours"] = contracted_hours_prior_year_df["hrs"]
    s["prior_year_contracted_fte"] = contracted_fte_prior_year

    return s


def _max_month_to_display(
    volumes: pd.DataFrame,
    uos: pd.DataFrame,
    income_stmt_df: pd.DataFrame,
) -> str:
    """
    Returns the latest month that we will display, which is where we have an income statement
    and volume or UOS data. If there is no volume or UOS data available, assume zero
    volume and use the month of the latest income statement.
    """
    cur_month = f"{date.today().year:04d}-{date.today().month:02d}"
    kpi_volumes = volumes if uos.empty else uos
    kpi_volumes_max = kpi_volumes["month"].max()
    kpi_volumes_max = "" if pd.isna(kpi_volumes_max) else kpi_volumes_max
    income_stmt_month_max = income_stmt_df["month"].max()

    month_max = min(kpi_volumes_max, income_stmt_month_max)
    month_max = cur_month if month_max == "" else month_max

    # Return month as a comparable string, like 2020-01, as well as year and month
    year, month = util.split_YYYY_MM(month_max)
    return month_max, year, month
