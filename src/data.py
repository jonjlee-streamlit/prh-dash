import logging
import pandas as pd
import streamlit as st
from dataclasses import dataclass
from .source_data import RawData, parse


@dataclass
class ProcessedData:
    """Represents processed data including"""

    # Original data set
    raw: RawData

    # Processed data set
    all: pd.DataFrame

    # Calculated statistics
    stats: dict


@st.cache_data(show_spinner=False)
def extract_from(files: list[str]) -> RawData:
    """
    Read and parse a list of source data files, including for example, Excel reports exported from Workday
    """
    # Read all files and merge data into one object
    segments = []
    for filename in files:
        # Fetch and read file into memory
        contents = _read_file(filename)
        segment = parse(filename, contents)
        segments.append(segment)

    raw_data = _merge(segments)
    return raw_data


def process(settings: dict, raw: RawData) -> ProcessedData:
    """
    Receives raw source data from extract_from() and user parameters from sidebar. Partitions and computes statistics to be displayed by the app.
    """
    stats = _calc_stats(settings, raw)
    return ProcessedData(raw=raw, all=None, stats=stats)


def _read_file(filename: str) -> bytes:
    """
    Wrapper for reading a source data file, returning data as byte array.
    In the future, will allow for fetching from URL and handling encrypted data.
    """
    logging.info("Fetching " + filename)
    with open(filename, "rb") as f:
        return f.read()


def _merge(segments: list[RawData]) -> RawData:
    """Merges data from several RawData objects which hold data from the source data files"""
    # Concatenate all DataFrames from segments
    income_statement = pd.concat([segment.income_statement for segment in segments], ignore_index=True)
    revenue = pd.concat([segment.revenue for segment in segments], ignore_index=True)
    deductions = pd.concat(
        [segment.deductions for segment in segments], ignore_index=True
    )
    expenses = pd.concat([segment.expenses for segment in segments], ignore_index=True)
    volume = pd.concat([segment.volume for segment in segments], ignore_index=True)
    hours = pd.concat([segment.hours for segment in segments], ignore_index=True)
    fte_per_pay_period = pd.concat(
        [segment.fte_per_pay_period for segment in segments], ignore_index=True
    )
    fte_hours_paid = pd.concat(
        [segment.fte_hours_paid for segment in segments], ignore_index=True
    )

    # Grab scalar values from each segment
    values = {k: v for segment in segments for k, v in segment.values.items()}

    # Create a new RawData instance with the concatenated DataFrame
    merged_data = RawData(
        income_statement=income_statement,
        revenue=revenue,
        deductions=deductions,
        expenses=expenses,
        volume=volume,
        hours=hours,
        fte_per_pay_period=fte_per_pay_period,
        fte_hours_paid=fte_hours_paid,
        values=values,
    )
    return merged_data


def _calc_stats(settings: dict, raw: RawData) -> dict:
    """Precalculate statistics from raw data that will be displayed on dashboard"""
    s = {
        # Totals rows from Income Statement
        "ytd_actual_revenue": raw.revenue["Actual (Year)"].iloc[-1],
        "ytd_budget_revenue": raw.revenue["Budget (Year)"].iloc[-1],
        "ytd_actual_deductions": raw.deductions["Actual (Year)"].iloc[-1],
        "ytd_budget_deductions": raw.deductions["Budget (Year)"].iloc[-1],
        "ytd_actual_net_revenue": raw.revenue["Actual (Year)"].iloc[-1]
        - raw.deductions["Actual (Year)"].iloc[-1],
        "ytd_budget_net_revenue": raw.revenue["Budget (Year)"].iloc[-1]
        - raw.deductions["Budget (Year)"].iloc[-1],
        "ytd_actual_expense": raw.expenses["Actual (Year)"].iloc[-1],
        "ytd_budget_expense": raw.expenses["Budget (Year)"].iloc[-1],
        # Totals column for Volume table, O4:O6
        "ytd_actual_volume": raw.volume.iloc[0, -1],
        "ytd_budget_volume": raw.volume.iloc[1, -1],
        # Totals column for Hours table, O22:O24
        # Productive hours are non-vacation hours that are attributed to staff
        "ytd_productive_hours": raw.hours.iloc[0, -1],
        "ytd_non_productive_hours": raw.hours.iloc[1, -1],
        # Totals column for FTE hours paid
        "pay_period_hours_paid": raw.fte_hours_paid.iloc[-1, 1],
        "ytd_hours_paid": raw.fte_hours_paid.iloc[-1, 2],
    }

    # KPIs
    s["actual_revenue_per_volume"] = (
        s["ytd_actual_net_revenue"] / s["ytd_actual_volume"]
    )
    s["target_revenue_per_volume"] = (
        s["ytd_budget_net_revenue"] / s["ytd_budget_volume"]
    )
    s["variance_revenue_per_volume"] = round(
        (s["actual_revenue_per_volume"] / s["target_revenue_per_volume"] - 1) * 100
    )

    s["actual_expense_per_volume"] = s["ytd_actual_expense"] / s["ytd_actual_volume"]
    s["target_expense_per_volume"] = s["ytd_budget_expense"] / s["ytd_budget_volume"]
    s["variance_expense_per_volume"] = round(
        (s["actual_expense_per_volume"] / s["target_expense_per_volume"] - 1) * 100
    )

    # Productivity. Standard target hours per volume is statically defined.
    s["actual_hours_per_volume"] = s["ytd_productive_hours"] / s["ytd_actual_volume"]
    s["target_hours_per_volume"] = settings["target_hours_per_volume"]
    s["variance_hours_per_volume"] = (
        s["target_hours_per_volume"] - s["actual_hours_per_volume"]
    )
    s["fte_variance"] = (s["variance_hours_per_volume"] * s["ytd_actual_volume"]) / (
        raw.values["std_fte_hours"] * raw.values["pct_hours_productive"]
    )
    s["fte_variance_dollars"] = (
        s["variance_hours_per_volume"] * s["ytd_actual_volume"]
    ) * (raw.values["avg_hourly_rate"])

    return s
