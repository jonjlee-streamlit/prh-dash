"""
This module contains functions to render various parts of the application, including the auth screen, 
sidebar for configuration options, main app content, etc.
"""
import streamlit as st
from . import data


def show_update(cur_files: list[str]) -> tuple[list | None, bool]:
    """
    Show the update data files screen
    """
    st.header("Update data files")
    st.markdown(
        '<a href="/" target="_self">Go to dashboard &gt;</a>', unsafe_allow_html=True
    )
    if cur_files:
        st.write("Current data files:")
        st.write(cur_files)
    remove_existing = st.checkbox("Remove existing files before upload")
    files = st.file_uploader("Select files to upload", accept_multiple_files=True)
    return files, remove_existing


def show_settings() -> dict:
    """
    Render the sidebar and return the dict with configuration options set by the user.
    """
    return {}


def show_main_content(settings: dict, data: data.ProcessedData):
    """
    Render main content of the app, given the user options from the side bar and pre-processed data.
    """
    st.title("Pullman Regional Hospital")

    st.header("KPIs")
    kpi_1, kpi_2, _kpi_3 = st.columns(3)
    kpi_1.metric(
        "Revenue per Encounter",
        "$%s" % round(data.stats["actual_revenue_per_volume"]),
        "%s%%" % data.stats["variance_revenue_per_volume"],
    )

    kpi_2.metric(
        "Expense per Encounter",
        "$%s" % round(data.stats["actual_expense_per_volume"]),
        delta="%s%%" % data.stats["variance_expense_per_volume"],
        delta_color="inverse",
    )
