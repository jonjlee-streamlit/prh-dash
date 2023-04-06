"""
Defines data classes that hold raw and processed source data
"""
import pandas as pd
from dataclasses import dataclass


@dataclass(eq=True, frozen=True)
class RawData:
    """Represents raw data read from Excel spreadsheets generated from various sources including Epic and Workday"""

    # Data from Workday
    revenue: pd.DataFrame
    deductions: pd.DataFrame
    expenses: pd.DataFrame

    # Volume data from Epic
    volume: pd.DataFrame
    hours: pd.DataFrame


@dataclass
class ProcessedData:
    """Represents processed data including"""

    # Original data set
    raw: RawData

    # Processed data set
    all: pd.DataFrame


def parse(filename: str, contents: bytes) -> RawData:
    """
    Detects the file type using a filename and its contents and converts it to a DataFrame containing the raw data.
    """
    # Read relevant sheets from the source Excel report
    income_stmt_df = pd.read_excel(contents, sheet_name="Income Statement", header=None)
    volume_stats_df = pd.read_excel(contents, sheet_name="STATS", header=None)

    revenue, deductions, expenses = _parse_income_stmt(income_stmt_df)
    volume, hours = _parse_volume_stats(volume_stats_df)

    return RawData(
        revenue=revenue,
        deductions=deductions,
        expenses=expenses,
        volume=volume,
        hours=hours,
    )


def _parse_income_stmt(df):
    """
    Read the Income Statement sheet from the source Excel report
    """
    # Column names from Excel sheet, columns B:J
    COLUMNS = [
        "Ledger Account",
        "Month Actual",
        "Month Budget",
        "Month Variance",
        "Month Variance %",
        "",
        "Year Actual",
        "Year Budget",
        "Year Variance",
        "Year Variance %",
    ]

    def _rows(df: pd.DataFrame, start_row_text: str, end_row_text: str) -> pd.DataFrame:
        """
        Extract a table embedded in an excel sheet between rows containing the string start_row_text and the row containing
        the string end_row_text. Excludes the start row, but includes the end row.
        Drops the separator column number separator_col.
        """
        start_row = df[df[0] == start_row_text].index[0] + 1
        end_row = df[df[0] == end_row_text].index[0]

        # Use loc to slice the DataFrame between start_row and end_row (in pandas, this includes both start and end)
        # First dimension is rows by index, second is all columns
        df = df.loc[start_row:end_row, :]

        # Drop empty separator column
        df.columns = COLUMNS
        df = df.drop(df.columns[5], axis=1)
        return df

    # Revenue table is from the rows containing "Operating Revenues" through "Total Revenue", excluding the first row
    revenue = _rows(df, "Operating Revenues", "Total Revenue")

    # Deductions table between "Deductions From Revenue" and "Total Deductions From Revenue"
    deductions = _rows(df, "Deductions From Revenue", "Total Deductions From Revenue")

    # Expenses table between "Expenses" and "Total Operating Expenses"
    expenses = _rows(df, "Expenses", "Total Operating Expenses")

    return revenue, deductions, expenses


def _parse_volume_stats(df):
    """
    Read the volume and productive/non-productive hours data from the source Excel report
    """
    # Column names from Excel sheet, columns B:N
    COLUMNS = [
        "Metric",
        "JAN",
        "FEB",
        "MAR",
        "APR",
        "MAY",
        "JUN",
        "JUL",
        "AUG",
        "SEP",
        "OCT",
        "NOV",
        "DEC",
        "Total",
    ]

    # Grab the data in B3:O6 (.loc first dimension is rows, second is columns)
    volume = df.loc[3:5, 1:14]
    volume.columns = COLUMNS

    # Grab the data in B22:O24
    hours = df.loc[21:23, 1:14]
    hours.columns = COLUMNS

    return volume, hours
