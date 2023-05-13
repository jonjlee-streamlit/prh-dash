import pandas as pd
from dataclasses import dataclass


@dataclass(eq=True, frozen=True)
class RawData:
    """Represents raw data read from Excel spreadsheets generated from various sources including Epic and Workday"""

    # Data from Workday
    income_statement: pd.DataFrame
    income_statements: list[pd.DataFrame]
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

    @staticmethod
    def merge(segments):
        """Merges data from several RawData objects which hold data from the source data files"""
        # Concatenate all DataFrames from segments
        income_statement = pd.concat(
            [segment.income_statement for segment in segments], ignore_index=True
        )
        income_statements = [income_statement for segment in segments for income_statement in segment.income_statements]
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
            income_statements=income_statements,
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
