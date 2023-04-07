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
    st.title("Rehabilitation Services")

    tab_1, tab_2 = st.tabs(["KPI & Productivity", "Calculations"])
    s = data.stats

    with tab_1:
        st.header("KPIs")
        kpi_1, kpi_2, _kpi_3 = st.columns(3)
        kpi_1.metric(
            "Revenue per Encounter",
            "$%s" % round(s["actual_revenue_per_volume"]),
            "%s%%" % s["variance_revenue_per_volume"],
        )

        kpi_2.metric(
            "Expense per Encounter",
            "$%s" % round(s["actual_expense_per_volume"]),
            delta="%s%%" % s["variance_expense_per_volume"],
            delta_color="inverse",
        )

        st.header("Productivity")
        prod_1, prod_2, prod_3 = st.columns(3)
        prod_1.metric("Hours per Encounter", round(s["actual_hours_per_volume"], 2))
        prod_2.metric("Target Hours per Encounter", s["target_hours_per_volume"])
        prod_3.metric("FTE Variance", round(s["fte_variance"], 2))

        prod_2.metric(
            "Dollar Impact",
            "$%s" % round(s["fte_variance_dollars"]),
        )

    with tab_2:
        st.write(s)
