import pandas as pd
import streamlit as st
from datetime import datetime
from dateutil.relativedelta import relativedelta
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

        month = st.selectbox(
            "Month",
            _prev_months(),
        )

    return {"dept": dept, "month": month}


def _prev_months():
    """Return the last 23 months in a format like ["Dec 2022", "Nov 2022", ...]."""
    today = datetime.now()
    ret = [datetime.now() - relativedelta(months=i) for i in range(25)]
    ret = [m.strftime("%b %Y") for m in ret]
    return ret


def show(settings: dict, data: data.RadsData):
    """
    Render main content for department
    """
    s = data.stats

    month = datetime.strptime(settings["month"], "%b %Y")
    month_str = datetime.strftime(month, "%B %Y")

    st.title(f"Radiology · {DEPT_ID_TO_NAME[settings['dept']]} · {month_str}")
    tab_income_stmt, tab_hours, tab_volumes = st.tabs(
        ["Income Statement", "FTE", "Volumes"]
    )

    with tab_income_stmt:
        _show_income_stmt(settings, data)
    with tab_volumes:
        _show_volumes(settings, data)
    with tab_hours:
        _show_hours(settings, data)


def _show_income_stmt(settings: dict, data: data.RadsData):
    if data.income_stmt is not None:
        figs.aggrid_income_stmt(data.income_stmt)
    else:
        st.write(f"No income statment data for this month")


def _show_volumes(settings: dict, data: data.RadsData):
    volume = data.stats.get("volume")
    volume = 0 if pd.isnull(volume) else volume

    st.metric(f"{settings['month']} Volume", volume)

    # Show graph of historical volumes. Allow user to select how many months to show.
    st.subheader("Volumes by Month")
    col_graph, col_period = st.columns((13, 3))
    with col_period:
        volumes_period = st.selectbox(
            label="Show",
            label_visibility="collapsed",
            options=["12 Months", "24 Months", "5 Years", "All"],
        )
    with col_graph:
        df = _filter_by_period(data.volumes, volumes_period, col_idx=0)
        figs.volumes_fig(df)


def _show_hours(settings, data):
    if data.hours is None or data.hours.shape[0] == 0:
        return st.write("No payroll hours data for this month")

    # Show productive / non-productive hours for month
    st.subheader("Hours")
    figs.hours_table(data.hours_for_month, data.hours_ytd)

    # Show graph of historical FTE. Allow user to select how many months to show.
    st.write("&nbsp;")
    st.subheader("FTE")
    col_graph, col_period = st.columns((13, 3))
    with col_period:
        fte_period = st.selectbox(
            key="fte_period",
            label="Show",
            label_visibility="collapsed",
            options=["12 Months", "24 Months", "5 Years", "All"],
        )

    with col_graph:
        df = _filter_by_period(data.hours, fte_period, 1)
        figs.fte_fig(df)


def _filter_by_period(df, period_str, col_idx):
    """
    Return data from the dataframe, df, with dates within the period_str, like "12 Months".
    Filter df based on the column number specified by col_idx.
    """
    if df is None:
        return None

    # Remove rows with non-datetime data in the first column
    df = df[pd.to_datetime(df.iloc[:, col_idx], errors="coerce").notnull()]

    # Filter based on first and last date. Treat None values as no filter.
    first_dt, last_dt = util.period_str_to_dates(period_str)
    if first_dt:
        df = df[df.iloc[:, col_idx] >= first_dt]
    if last_dt:
        df = df[df.iloc[:, col_idx] <= last_dt]
    return df
