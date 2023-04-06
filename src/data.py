import logging
import pandas as pd
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


def process(raw: RawData) -> ProcessedData:
    """
    Receives raw source data from extract_from(). Partitions and computes statistics to be displayed by the app.
    """
    stats = _calc_stats(raw)
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
    revenue = pd.concat([segment.revenue for segment in segments], ignore_index=True)
    deductions = pd.concat(
        [segment.deductions for segment in segments], ignore_index=True
    )
    expenses = pd.concat([segment.expenses for segment in segments], ignore_index=True)
    volume = pd.concat([segment.volume for segment in segments], ignore_index=True)
    hours = pd.concat([segment.hours for segment in segments], ignore_index=True)

    # Grab scalar values from each segment
    values = {k: v for segment in segments for k, v in segment.values.items()}

    # Create a new RawData instance with the concatenated DataFrame
    merged_data = RawData(
        revenue=revenue,
        deductions=deductions,
        expenses=expenses,
        volume=volume,
        hours=hours,
        values=values,
    )
    return merged_data


def _calc_stats(raw: RawData) -> dict:
    """Precalculate statistics from raw data that will be displayed on dashboard"""
    v = {
        # Totals rows from Income Statement
        "ytd_actual_revenue": raw.revenue["Year Actual"].iloc[-1],
        "ytd_budget_revenue": raw.revenue["Year Budget"].iloc[-1],
        "ytd_actual_deductions": raw.deductions["Year Actual"].iloc[-1],
        "ytd_budget_deductions": raw.deductions["Year Budget"].iloc[-1],
        "ytd_actual_net_revenue": raw.revenue["Year Actual"].iloc[-1]
        - raw.deductions["Year Actual"].iloc[-1],
        "ytd_budget_net_revenue": raw.revenue["Year Budget"].iloc[-1]
        - raw.deductions["Year Budget"].iloc[-1],
        "ytd_actual_expense": raw.expenses["Year Actual"].iloc[-1],
        "ytd_budget_expense": raw.expenses["Year Budget"].iloc[-1],
        # Totals column for Volume table, O4:O6
        "ytd_actual_volume": raw.volume.iloc[0, -1],
        "ytd_budget_volume": raw.volume.iloc[1, -1],
        # Totals column for Hours table, O22:O24
        # Productive hours are non-vacation hours that are attributed to staff
        "ytd_productive_hours": raw.hours.iloc[0, -1],
        "ytd_non_productive_hours": raw.hours.iloc[1, -1],
    }

    # KPIs
    v["actual_revenue_per_volume"] = (
        v["ytd_actual_net_revenue"] / v["ytd_actual_volume"]
    )
    v["budget_revenue_per_volume"] = (
        v["ytd_budget_net_revenue"] / v["ytd_budget_volume"]
    )
    v["variance_revenue_per_volume"] = (
        v["actual_revenue_per_volume"] / v["budget_revenue_per_volume"] - 1
    )

    v["actual_expense_per_volume"] = v["ytd_actual_expense"] / v["ytd_actual_volume"]
    v["budget_expense_per_volume"] = v["ytd_budget_expense"] / v["ytd_budget_volume"]
    v["variance_expense_per_volume"] = (
        v["actual_expense_per_volume"] / v["budget_expense_per_volume"] - 1
    )

    # Productivity. Standard target hours per volume is statically defined.
    v["actual_hours_per_volume"] = v["ytd_productive_hours"] / v["ytd_actual_volume"]
    v["target_hours_per_volume"] = 4.24
    v["variance_hours_per_volume"] = (
        v["target_hours_per_volume"] - v["actual_hours_per_volume"]
    )
    v["fte_variance"] = (v["variance_hours_per_volume"] * v["ytd_actual_volume"]) / (
        raw.values["std_fte_hours"] * raw.values["pct_hours_productive"]
    )
    v["fte_variance_dollars"] = (
        v["variance_hours_per_volume"] * v["ytd_actual_volume"]
    ) * (raw.values["avg_hourly_rate"])

    return v
