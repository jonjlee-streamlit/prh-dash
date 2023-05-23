"""
Utility functions
"""
import streamlit as st
import pandas as pd
import typing
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


def df_get_tables_by_columns(
    df: pd.DataFrame, rows: str
) -> typing.Iterator[pd.DataFrame]:
    """
    Yields dataframes representing tables in the original dataframe based on specified rows.
    rows is specified in Excel A1-notation, eg. 5:10
    """
    start_col = 0
    row_indices = _row_ranges_to_list(rows)

    while True:
        # Find the next nonempty column after the current start_col
        nonempty_col = df_next_nonempty_col(df, rows, start_col_idx=start_col)

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
        yield table

        # Start next iteration from the first empty column after the table
        start_col = empty_col


def df_next_empty_row(df: pd.DataFrame, columns: str, start_row_idx: int = 0) -> int:
    """
    Given a dataframe, starting row offset, and set of columns, returns the next row index where all the columns are empty.
    columns is specified in Excel A1-notation, eg. A:F,AB,ZZ
    """
    # Convert the columns from Excel A1-notation to column indices
    column_indices = _col_ranges_to_list(columns)

    # Iterate over the rows starting from the specified row
    for row in range(start_row_idx, df.shape[0]):
        row_data = df.iloc[row, column_indices]
        if row_data.isnull().all():
            return row

    # Return -1 if no empty row is found
    return -1


def df_next_empty_col(df: pd.DataFrame, rows: str, start_col_idx: int = 0) -> int:
    """
    Given a dataframe, starting column offset, and set of rows, returns the next column index where all the rows are empty.
    rows is specified in Excel A1-notation or row numbers (first row is 1), eg. 1:5,10,15
    """
    # Convert the rows from Excel A1-notation to row indices
    row_indices = _row_ranges_to_list(rows)

    # Iterate over the columns starting from the specified column
    for col in range(start_col_idx, df.shape[1]):
        col_data = df.iloc[row_indices, col]
        if col_data.isnull().all():
            return col

    # Return -1 if no empty column is found
    return -1


def df_next_nonempty_col(df: pd.DataFrame, rows: str, start_col_idx: int = 0) -> int:
    """
    Given a dataframe, starting column offset, and set of rows, returns the next column index where all the rows are empty.
    rows is specified in Excel A1-notation or row numbers (first row is 1), eg. 1:5,10,15
    """
    # Convert the rows from Excel A1-notation to row indices
    row_indices = _row_ranges_to_list(rows)

    # Iterate over the columns starting from the specified column
    for col in range(start_col_idx, df.shape[1]):
        col_data = df.iloc[row_indices, col]
        if not col_data.isnull().all():
            return col

    # Return -1 if no non-empty column is found
    return -1


def _col_ranges_to_list(columns: str) -> list[int]:
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


def _row_ranges_to_list(rows: str) -> list[int]:
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
