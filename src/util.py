"""
Utility functions
"""
import streamlit as st
import pandas as pd
from openpyxl.utils import cell
import re


def df_get_val_or_range(df, cell_range):
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
