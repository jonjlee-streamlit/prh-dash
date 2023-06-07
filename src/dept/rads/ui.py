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
            ),
            format_func=DEPT_ID_TO_NAME.get,
        )

        month = st.selectbox("Month", _prev_months(), 2)

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
    tab_kpi, tab_income_stmt, tab_hours, tab_volumes = st.tabs(
        ["KPI & Productivity", "Income Statement", "FTE", "Volumes"]
    )

    with tab_kpi:
        _show_kpi(settings, data)
    with tab_income_stmt:
        _show_income_stmt(settings, data)
    with tab_volumes:
        _show_volumes(settings, data)
    with tab_hours:
        _show_hours(settings, data)


def _show_kpi(settings: dict, data: data.RadsData):
    s = data.stats

    st.subheader("KPIs")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric(
        "Revenue per Exam",
        "$%s" % round(s["revenue_per_volume"]),
        f"{s['variance_revenue_per_volume']}% {'above' if s['revenue_per_volume'] >= s['target_revenue_per_volume'] else 'below'} target",
    )
    col2.metric(
        "Target Revenue per Exam", "$%s" % round(s["target_revenue_per_volume"])
    )

    col1, col2, col3, col4 = st.columns(4)
    col1.metric(
        "Expense per Encounter",
        "$%s" % round(s["expense_per_volume"]),
        delta=f"{s['variance_expense_per_volume']}% {'above' if s['expense_per_volume'] >= s['target_expense_per_volume'] else 'below'} target",
        delta_color="inverse",
    )
    col2.metric(
        "Target Expense per Encounter",
        f"${round(s['target_expense_per_volume'])}",
    )

    st.subheader("Productivity")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Hours per Exam", round(s["hours_per_volume"], 2))
    col2.metric("Target Hours per Exam", s["target_hours_per_volume"])
    col1.metric("FTE Variance", round(s["fte_variance"], 2))

    v = s["fte_variance_dollars"]
    color = "rgb(255, 43, 43)" if v < 0 else "rgb(9, 171, 59)"
    col2.markdown(
        "<p style='font-size:14px;'>Dollar Impact</p>"
        + f"<p style='margin-top:-15px; font-size:2rem; color:{color}'>{util.format_finance(v)}</p>"
        + f"<p style='margin-top:-15px; font-size:14px;'>using avg hourly rate $37.06</p>",
        unsafe_allow_html=True,
    )


def _show_income_stmt(settings: dict, data: data.RadsData):
    col_month, col_ytd = st.columns(2)
    with col_month:
        st.subheader(settings["month"])
        if data.income_stmt is not None:
            figs.aggrid_income_stmt(data.income_stmt)
        else:
            st.write(f"No data for this month")

    with col_ytd:
        st.subheader("YTD")
        if data.income_stmt_ytd is not None:
            figs.aggrid_income_stmt(data.income_stmt_ytd)
        else:
            st.write(f"No data for this department")


def _show_volumes(settings: dict, data: data.RadsData):
    st.subheader("Summary")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric(f"{settings['month']} Volume", data.stats["month_volume"])
    col2.metric(f"YTD Volume", data.stats["ytd_volume"])

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
        return st.write("No data for this month")

    # Show productive / non-productive hours for month
    st.subheader("Summary")
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
        figs.fte_fig(df, data.stats["budget_fte"])


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
