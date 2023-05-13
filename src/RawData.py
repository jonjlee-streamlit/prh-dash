import pandas as pd
from dataclasses import dataclass


@dataclass(eq=True, frozen=True)
class RawData:
    """Represents raw data read from Excel spreadsheets generated from various sources including Epic and Workday"""

    # Data from Workday
    income_statement: pd.DataFrame
    revenue: pd.DataFrame
    deductions: pd.DataFrame
    expenses: pd.DataFrame

    # Volume data from Epic
    volume: pd.DataFrame
    hours: pd.DataFrame
    values: dict

    # FTE Report
    fte_per_pay_period: pd.DataFrame
    fte_hours_paid: pd.DataFrame