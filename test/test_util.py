import pandas as pd
from src.util import *


def test_df_get_tables_by_columns():
    # Empty DataFrame
    empty_df = pd.DataFrame()
    assert len(df_get_tables_by_columns(empty_df, "1:2")) == 0

    # Test data - use transpose() so we can visualize the data in rows in the code here
    df = pd.DataFrame(
        {
            "row1": [None, None, None, None, None, None, None, None, None, None],
            "row2": [None, "xx", "xx", None, None, None, "xx", "xx", None, "xx"],
            "row3": [None, None, "xx", "xx", None, None, None, None, None, "xx"],
            "row4": [None, None, None, None, None, None, "xx", None, None, "xx"],
            "row5": [None, None, None, None, None, None, None, None, None, None],
        }
    ).transpose()

    # Find all tables of the correct size
    tables = df_get_tables_by_columns(df, "2:4")
    assert tables[0].shape == (3, 3)
    assert tables[1].shape == (3, 2)
    assert tables[2].shape == (3, 1)


def test_df_get_tables_by_rows():
    # Empty DataFrame
    empty_df = pd.DataFrame()
    assert len(df_get_tables_by_rows(empty_df, "A:B")) == 0

    # Test data - use transpose() so we can visualize the data in rows in the code here
    df = pd.DataFrame(
        {
            "row1": [None, None, None, None, None],
            "row2": [None, "xx", "xx", "xx", None],
            "row3": [None, None, "xx", None, None],
            "row4": [None, None, "xx", None, None],
            "row5": [None, None, None, None, None],
            "row6": [None, None, None, None, None],
            "row7": [None, "xx", None, None, None],
            "row8": [None, None, "xx", None, None],
            "row9": [None, None, None, None, None],
            "row0": [None, None, None, "xx", None],
        }
    ).transpose()

    # Find all tables of the correct size
    tables = df_get_tables_by_rows(df, "B:D")
    assert tables[0].shape == (3, 3)
    assert tables[1].shape == (2, 3)
    assert tables[2].shape == (1, 3)


def test_df_next_empty_row():
    # Empty DataFrame
    empty_df = pd.DataFrame()
    assert df_next_empty_row(empty_df, "B:C") == -1

    # Test data
    df = pd.DataFrame(
        {
            "col1": [1, 2, 3],
            "col2": [None, 4, None],
            "col3": [None, None, None],
            "col4": [None, None, None],
            "col5": [None, None, None],
        }
    )

    # Address 1 column
    assert df_next_empty_row(df, "C") == 0

    # Address 1 column range
    assert df_next_empty_row(df, "C:D") == 0

    # Address multiple column ranges
    assert df_next_empty_row(df, "B:C,D:E") == 0

    # Address column range + single column
    assert df_next_empty_row(df, "C:D,E") == 0

    # No empty rows
    assert df_next_empty_row(df, "A:B") == -1

    # Test that starting row offset works
    assert df_next_empty_row(df, "B:C", start_row_idx=1) == 2

    # Starting starting row offset is out of range
    assert df_next_empty_row(df, "A:C", start_row_idx=5) == -1


def test_df_next_row():
    # Empty DataFrame
    empty_df = pd.DataFrame()
    assert df_next_row(empty_df, "A:A") == -1

    # Test data
    df = pd.DataFrame(
        {
            "row1": [1, None, None, None],
            "row2": [None, None, None, None],
            "row3": [None, None, None, None],
            "row4": [2, None, None, None],
            "row5": [None, None, None, None],
        }
    ).transpose()

    # One non-empty row
    assert df_next_row(df, "A:B") == 0

    # No non-empty rows
    assert df_next_row(df, "B:C") == -1

    # Test that starting row offset works
    assert df_next_row(df, "A:B", start_row_idx=1) == 3

    # Starting starting row offset is out of range
    assert df_next_row(df, "A:B", start_row_idx=5) == -1


def test_df_next_empty_col():
    # Empty DataFrame
    empty_df = pd.DataFrame()
    assert df_next_empty_col(empty_df, "1:1") == -1

    # Test data
    df = pd.DataFrame(
        {
            "row1": [1, None, 3, 4],
            "row2": [None, 2, None, 5],
            "row3": [None, None, None, None],
            "row4": [None, None, None, None],
            "row5": [None, None, None, None],
        }
    ).transpose()

    # Address 1 row
    assert df_next_empty_col(df, "3") == 0

    # Address 1 row range
    assert df_next_empty_col(df, "3:4") == 0

    # Address multiple row ranges
    assert df_next_empty_col(df, "2:3,4:5") == 0

    # Address row range + single row
    assert df_next_empty_col(df, "3:4,5") == 0

    # No empty columns
    assert df_next_empty_col(df, "1:2") == -1

    # Test that starting column offset works
    assert df_next_empty_col(df, "2:3", start_col_idx=1) == 2

    # Starting starting column offset is out of range
    assert df_next_empty_col(df, "1:3", start_col_idx=5) == -1


def test_df_next_col():
    # Empty DataFrame
    empty_df = pd.DataFrame()
    assert df_next_col(empty_df, "1:1") == -1

    # Test data
    df = pd.DataFrame(
        {
            "row1": [1, None, None, 2],
            "row2": [None, None, None, None],
            "row3": [None, None, None, None],
            "row4": [None, None, None, None],
            "row5": [None, None, None, None],
        }
    ).transpose()

    # One non-empty column
    assert df_next_col(df, "1:2") == 0

    # No non-empty columns
    assert df_next_col(df, "2:3") == -1

    # Test that starting column offset works
    assert df_next_col(df, "1:4", start_col_idx=1) == 3

    # Starting starting column offset is out of range
    assert df_next_col(df, "1:3", start_col_idx=5) == -1
