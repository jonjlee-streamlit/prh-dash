import pandas as pd
import streamlit as st
from datetime import datetime
from dateutil.relativedelta import relativedelta
from . import configs, data, figs
from ... import util, static_data


def show_settings(config: configs.DeptConfig) -> dict:
    """
    Render the sidebar and return the dict with configuration options set by the user.
    """

    def dept_id_to_name(id):
        return (
            id
            if id == "All"
            else static_data.WDID_TO_DEPT_NAME.get(id) or f"Unknown Department {id}"
        )

    with st.sidebar:
        util.st_sidebar_prh_logo()

        if len(config.wd_ids) > 1:
            dept_id = st.selectbox(
                "Department",
                options=["All"] + config.wd_ids,
                format_func=dept_id_to_name,
            )
        else:
            dept_id = config.wd_ids[0]

        month = st.selectbox(
            "Month",
            options=_prev_months(24),
            format_func=lambda m: datetime.strptime(m, "%Y-%m").strftime("%b %Y"),
        )

    return {"dept_id": dept_id, "dept_name": dept_id_to_name(dept_id), "month": month}


def _prev_months(n_months):
    """
    Return the last n_months in a format like ["2022-12", "2022-11", ...]
    """
    ret = [datetime.now() - relativedelta(months=i + 1) for i in range(n_months)]
    ret = [m.strftime("%Y-%m") for m in ret]
    return ret


def show(config: configs.DeptConfig, settings: dict, data: data.DeptData):
    """
    Render main content for department
    """
    s = data.stats

    # Reformat selected month in sidebar from "2023-01" to "Jan 2023"
    month = datetime.strptime(settings["month"], "%Y-%m")
    month_str = datetime.strftime(month, "%B %Y")

    # Title with department name, sub-department, and month. e.g. "Imaging - CT - January 2023"
    if len(config.wd_ids) > 1:
        st.title(f"{config.name} · {settings['dept_name']} · {month_str}")
    else:
        st.title(f"{config.name} · {month_str}")

    # Main content tabs
    tab_kpi, tab_income_stmt, tab_hours, tab_volumes = st.tabs(
        ["KPI & Productivity", "Income Statement", "FTE", "Volumes"]
    )
    with tab_kpi:
        _show_kpi(settings, data)


def _show_kpi(settings: dict, data: data.DeptData):
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
    col2.metric("Target Hours per Exam", round(s["target_hours_per_volume"], 2))
    col1.metric("FTE Variance", round(s["fte_variance"], 2))

    v = s["fte_variance_dollars"]
    color = "rgb(255, 43, 43)" if v < 0 else "rgb(9, 171, 59)"
    col2.markdown(
        "<p style='font-size:14px;'>Dollar Impact</p>"
        + f"<p style='margin-top:-15px; font-size:2rem; color:{color}'>{util.format_finance(v)}</p>"
        + f"<p style='margin-top:-15px; font-size:14px;'>using avg hourly rate $37.06</p>",
        unsafe_allow_html=True,
    )
