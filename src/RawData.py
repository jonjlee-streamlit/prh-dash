import pandas as pd
from dataclasses import dataclass, field


@dataclass(eq=True, frozen=True)
class RawData:
    """Represents raw data read from Excel spreadsheets generated from various sources including Epic and Workday"""

    # Data from Workday
    income_statement: pd.DataFrame = None
    income_statements: list[pd.DataFrame] = field(default_factory=list)
    revenue: pd.DataFrame = None
    deductions: pd.DataFrame = None
    expenses: pd.DataFrame = None

    # Historical volume data from Excel
    rads_volumes: list[pd.DataFrame] = field(default_factory=list)

    # Volume data from Epic
    volume: pd.DataFrame = None
    hours: pd.DataFrame = None
    values: dict = field(default_factory=dict)

    # FTE Report
    fte_per_pay_period: pd.DataFrame = None
    fte_hours_paid: pd.DataFrame = None

    # Produtive / non-productive hour tables
    hours_by_pay_period: list[pd.DataFrame] = field(default_factory=list)
    hours_by_month: list[pd.DataFrame] = field(default_factory=list)

    @staticmethod
    def merge(segments):
        """Merges data from several RawData objects which hold data from the source data files"""
        # Concatenate all DataFrames from segments
        income_statement = pd.concat(
            [segment.income_statement for segment in segments], ignore_index=True
        )
        revenue = pd.concat(
            [segment.revenue for segment in segments], ignore_index=True
        )
        deductions = pd.concat(
            [segment.deductions for segment in segments], ignore_index=True
        )
        expenses = pd.concat(
            [segment.expenses for segment in segments], ignore_index=True
        )
        volume = pd.concat([segment.volume for segment in segments], ignore_index=True)
        hours = pd.concat([segment.hours for segment in segments], ignore_index=True)
        fte_per_pay_period = pd.concat(
            [segment.fte_per_pay_period for segment in segments], ignore_index=True
        )
        fte_hours_paid = pd.concat(
            [segment.fte_hours_paid for segment in segments], ignore_index=True
        )
        income_statements = []
        rads_volumes = []
        hours_by_pay_period = []
        hours_by_month = []
        for seg in segments:
            income_statements += seg.income_statements
            rads_volumes += seg.rads_volumes
            hours_by_pay_period += seg.hours_by_pay_period
            hours_by_month += seg.hours_by_month

        # Grab scalar values from each segment
        values = {k: v for segment in segments for k, v in segment.values.items()}

        # Create a new RawData instance with the concatenated DataFrame
        merged_data = RawData(
            income_statement=income_statement,
            income_statements=income_statements,
            revenue=revenue,
            deductions=deductions,
            expenses=expenses,
            rads_volumes=rads_volumes,
            volume=volume,
            hours=hours,
            fte_per_pay_period=fte_per_pay_period,
            fte_hours_paid=fte_hours_paid,
            hours_by_pay_period=hours_by_pay_period,
            hours_by_month=hours_by_month,
            values=values,
        )
        return merged_data
