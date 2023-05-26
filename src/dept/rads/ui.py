import streamlit as st
from .data import RadsData
from ... import util

def show_settings() -> dict:
    """
    Render the sidebar and return the dict with configuration options set by the user.
    """
    with st.sidebar:
        util.st_sidebar_prh_logo()
        dept = st.selectbox("Department", ["MRI", "CT", "Imaging Services", "Ultrasound", "Mammography", "Nuclear Medicine"])
        period = st.selectbox("Period", ["Month to Date", "Year to Date", "12 months", "24 months", "All"])

    return {
        "department": dept,
        "period": period
    }


def show(settings: dict, data: RadsData):
    """
    Render main content for department
    """
    s = data.stats

    st.title("Radiology")
    tab_income_stmt, tab_hours = st.tabs(
        ["Income Statement", "Hours"]
    )

    with tab_income_stmt:
        _show_income_stmt(settings, data)
    with tab_hours:
        _show_hours(settings, data)


def _show_income_stmt(settings, data):
    st.subheader("Revenue")

def _show_hours(settings, data):
    pass