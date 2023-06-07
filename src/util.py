"""
Utility functions
"""
import typing
import streamlit as st
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta
from openpyxl.utils import cell
import re


# ----------------------------------
# Pandas functions
# ----------------------------------
def df_get_val_or_range(df: pd.DataFrame, cell_range: str) -> pd.DataFrame:
    """
    Returns a subset of a dataframe using excel-like A1 notation.
    If given a range, returns a dataframe.
    If given a single location, returns the value.
    For example, df_get_range(df, "B2") returns the value in column 2, row 2,
    and df_get_range(df, "B2:D5") returns a dataframe with data from columns 2-4, rows 2-5.
    """
    # Check if provided range is a single coordinate or range
    if ":" in cell_range:
        cell_refs = re.split("[:]", cell_range)
        start_row, start_col = cell.coordinate_to_tuple(cell_refs[0])
        end_row, end_col = cell.coordinate_to_tuple(cell_refs[1])

        return df.iloc[start_row - 1 : end_row, start_col - 1 : end_col]
    else:
        row, col = cell.coordinate_to_tuple(cell_range)
        return df.iloc[row - 1, col - 1]


def df_get_tables_by_columns(df: pd.DataFrame, rows: str) -> list[pd.DataFrame]:
    """
    REturns a list of dataframes representing tables in the original dataframe based on specified rows.
    rows is specified in Excel A1-notation, eg. 5:10
    """
    ret = []
    start_col = 0
    row_indices = _rows_A1_to_idx_list(rows)

    while True:
        # Find the next nonempty column after the current start_col
        nonempty_col = df_next_col(df, rows, start_col_idx=start_col)

        # Exit if no more data in columns
        if nonempty_col == -1:
            break

        # Find the next empty column after the nonempty_col
        empty_col = df_next_empty_col(df, rows, start_col_idx=nonempty_col)

        # If no more empty columns are found, use the entire remaining columns
        if empty_col == -1:
            empty_col = df.shape[1]

        # Extract the table as a dataframe and yield it
        table = df.iloc[row_indices, nonempty_col:empty_col]
        ret.append(table)

        # Start next iteration from the first empty column after the table
        start_col = empty_col

    return ret


def df_get_tables_by_rows(
    df: pd.DataFrame, cols: str, start_row_idx: int = 0
) -> list[pd.DataFrame]:
    """
    Yields dataframes representing tables in the original dataframe with data in specified columns.
    cols is specified in Excel A1-notation, eg. A:F
    """
    ret = []
    start_row = start_row_idx
    col_indices = _cols_A1_to_idx_list(cols)

    while True:
        # Find the next nonempty row after the current start_row
        nonempty_row = df_next_row(df, cols, start_row_idx=start_row)

        # Exit if no more data in rows
        if nonempty_row == -1:
            break

        # Find the next empty row after the nonempty_col
        empty_row = df_next_empty_row(df, cols, start_row_idx=nonempty_row)

        # If no more empty rows are found, use the entire remaining rows
        if empty_row == -1:
            empty_row = df.shape[0]

        # Extract the table as a dataframe and yield it
        table = df.iloc[nonempty_row:empty_row, col_indices]
        ret.append(table)

        # Start next iteration from the first empty row after the table
        start_row = empty_row

    return ret


def df_next_row(
    df: pd.DataFrame, columns: str, start_row_idx: int = 0, find_empty: bool = False
) -> int:
    """
    Given a dataframe, starting row offset, and set of columns, returns the next row index where there is data in one of the columns.
    columns is specified in Excel A1-notation, eg. A:F,AB,ZZ
    If find_empty is True, then returns next row where all the columns are empty
    """
    # Convert the columns from Excel A1-notation to column indices
    column_indices = _cols_A1_to_idx_list(columns)

    # Iterate over the rows starting from the specified row
    for row in range(start_row_idx, df.shape[0]):
        row_data = df.iloc[row, column_indices]
        if (not find_empty and not row_data.isnull().all()) or (
            find_empty and row_data.isnull().all()
        ):
            # Return index of either first non-empty or empty row, depending on find_empty parameter
            return row

    # Return -1 if no empty row is found
    return -1


def df_next_empty_row(df: pd.DataFrame, columns: str, start_row_idx: int = 0) -> int:
    """
    Given a dataframe, starting row offset, and set of columns, returns the next row index where all the columns are empty.
    columns is specified in Excel A1-notation, eg. A:F,AB,ZZ
    """
    return df_next_row(df, columns, start_row_idx, True)


def df_next_col(
    df: pd.DataFrame, rows: str, start_col_idx: int = 0, find_empty: bool = False
) -> int:
    """
    Given a dataframe, starting column offset, and set of rows, returns the next column index where there is data in one of the rows.
    rows is specified in Excel A1-notation or row numbers (first row is 1), eg. 1:5,10,15
    If find_empty is True, then returns next column where all the rows are empty
    """
    # Convert the rows from Excel A1-notation to row indices
    row_indices = _rows_A1_to_idx_list(rows)

    # Iterate over the columns starting from the specified column
    for col in range(start_col_idx, df.shape[1]):
        col_data = df.iloc[row_indices, col]
        if (not find_empty and not col_data.isnull().all()) or (
            find_empty and col_data.isnull().all()
        ):
            return col

    # Return -1 if no non-empty column is found
    return -1


def df_next_empty_col(df: pd.DataFrame, rows: str, start_col_idx: int = 0) -> int:
    """
    Given a dataframe, starting column offset, and set of rows, returns the next column index where all the rows are empty.
    rows is specified in Excel A1-notation or row numbers (first row is 1), eg. 1:5,10,15
    """
    return df_next_col(df, rows, start_col_idx, True)


def _cols_A1_to_idx_list(columns: str) -> list[int]:
    """
    Given a set of columns in Excel A1-notation or single row numbers, eg A:F,AB,ZZ
    return a list of 0-based row indexes in the range.
    """
    column_indices = []
    for column_range in columns.split(","):
        if ":" in column_range:
            start_col, end_col = column_range.split(":")
            column_indices.extend(
                range(
                    cell.column_index_from_string(start_col) - 1,
                    cell.column_index_from_string(end_col),
                )
            )
        else:
            column_indices.append(cell.column_index_from_string(column_range) - 1)
    return column_indices


def _rows_A1_to_idx_list(rows: str) -> list[int]:
    """
    Given a set of rows in Excel A1-notation or single row numbers, eg 1:5,10,15 (note, A1 row numbers are 1-based)
    return a list of 0-based row indexes in the range.
    """
    row_indices = []
    for row_range in rows.split(","):
        if ":" in row_range:
            start_row, end_row = row_range.split(":")
            row_indices.extend(range(int(start_row) - 1, int(end_row)))
        else:
            row_indices.append(int(row_range) - 1)
    return row_indices


# -----------------------------------
# Streamlit functions
# -----------------------------------
def st_prh_logo():
    """
    Add PRH Logo
    """
    st.image(
        "https://www.pullmanregional.org/hubfs/PullmanRegionalHospital_December2019/Image/logo.svg"
    )


def st_sidebar_prh_logo():
    """
    Add PRH Logo to side bar - https://discuss.streamlit.io/t/put-logo-and-title-above-on-top-of-page-navigation-in-sidebar-of-multipage-app/28213/5
    """
    st.markdown(
        """
        <style>
            [data-testid="stSidebar"] {
                background-image: url(https://www.pullmanregional.org/hubfs/PullmanRegionalHospital_December2019/Image/logo.svg);
                background-repeat: no-repeat;
                padding-top: 0px;
                background-position: 80px 20px;
            }
            .element-container iframe {
                min-height: 810px;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


# -----------------------------------
# Date/time functions
# -----------------------------------
def period_str_to_dates(dates: str) -> typing.Tuple[datetime, datetime]:
    """
    Convert a time period string, such as "Month to Date", "Last 12 Months", etc
    to start and end date objects. Returns a tuple (first date, last date)
    """
    dates = dates.lower()
    today = datetime.today()
    today = today.replace(hour=0, minute=0, second=0, microsecond=0)
    last_day_of_month = today + relativedelta(day=31)
    last_day_of_month = last_day_of_month.replace(
        hour=23, minute=59, second=59, microsecond=999
    )

    if dates == "month to date":
        first_date = today - relativedelta(months=5)
        first_date = datetime(first_date.year, first_date.month, 1)
        return first_date, last_day_of_month
    elif dates == "year to date":
        first_date = datetime(today.year, 1, 1)
        return first_date, last_day_of_month
    elif dates == "last year":
        last_year = today.year - 1
        first_date = datetime(last_year, 1, 1)
        last_date = datetime(last_year, 12, 31)
        return first_date, last_date
    elif dates == "12 months":
        first_date = datetime(today.year - 1, today.month, 1)
        return first_date, last_day_of_month
    elif dates == "24 months":
        first_date = datetime(today.year - 2, today.month, 1)
        return first_date, last_day_of_month
    elif dates == "5 years":
        first_date = datetime(today.year - 5, today.month, 1)
        return first_date, last_day_of_month
    else:
        return None, None


# -----------------------------------
# Finance functions
# -----------------------------------
def format_finance(n):
    """Return a number formatted a finance amount - dollar sign, two decimal places, commas, negative values wrapped in parens"""
    return "${0:,.2f}".format(n) if n >= 0 else "(${0:,.2f})".format(abs(n))
