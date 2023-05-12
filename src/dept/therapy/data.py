import pandas as pd
from dataclasses import dataclass
from ...source_data import RawData


@dataclass
class TherapyData:
    """Represents processed data including"""

    # Original data set
    raw: RawData

    # Calculated statistics
    stats: dict


def process(settings: dict, raw: RawData) -> TherapyData:
    """
    Receives raw source data from extract_from() and user parameters from sidebar. Partitions and computes statistics to be displayed by the app.
    """
    stats = _calc_stats(settings, raw)
    return TherapyData(raw=raw, stats=stats)

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
