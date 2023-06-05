import streamlit as st
from . import data, figs
from ... import util

# Convert department ID to readable labels
DEPT_ID_TO_NAME = {
    data.DEPT_XR: "XR",
    data.DEPT_CT: "CT",
    data.DEPT_MRI: "MRI",
    data.DEPT_ULTRASOUND: "Ultrasound",
    data.DEPT_NUCLEAR: "Nuclear Medicine",
    data.DEPT_MAMMOGRAPHY: "Mammography",
    data.DEPT_IMAGING_SERVICES: "Imaging Services",
}


def show_settings() -> dict:
    """
    Render the sidebar and return the dict with configuration options set by the user.
    """
    with st.sidebar:
        util.st_sidebar_prh_logo()

        dept = st.selectbox(
            "Department",
            options=(
                data.DEPT_CT,
                data.DEPT_XR,
                data.DEPT_MRI,
                data.DEPT_ULTRASOUND,
                data.DEPT_NUCLEAR,
                data.DEPT_MAMMOGRAPHY,
                data.DEPT_IMAGING_SERVICES,
            ),
            format_func=DEPT_ID_TO_NAME.get,
        )

        period = st.selectbox(
            "Period", ["Month to Date", "Year to Date", "12 months", "24 months", "All"]
        )

    return {"dept": dept, "period": period}


def show(settings: dict, data: data.RadsData):
    """
    Render main content for department
    """
    s = data.stats

    st.title(f"Radiology - {DEPT_ID_TO_NAME[settings['dept']]}")
    tab_income_stmt, tab_hours = st.tabs(["Income Statement", "Hours"])

    with tab_income_stmt:
        _show_income_stmt(settings, data)
    with tab_hours:
        _show_hours(settings, data)


def _show_income_stmt(settings: dict, data: data.RadsData):
    if settings["dept"] in data.income_stmt_by_dept:
        st.markdown(
            f"<center><span style=\"font-size:20pt;\">Period: {settings['period']}</span></center>",
            unsafe_allow_html=True,
        )
        figs.aggrid_income_stmt(data.income_stmt_by_dept[settings["dept"]])
    else:
        st.write(f"No income statment data for department")


def _show_hours(settings, data):
    pass


data
