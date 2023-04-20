"""
This module contains functions to render various parts of the application, including the auth screen, 
sidebar for configuration options, main app content, etc.
"""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
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
    # with st.sidebar:
    #     st.header("Dashboard Settings")
    #     target_hours_per_volume = st.slider(
    #         "Target Man-Hours per Encounter", 2.0, 10.0, 4.24
    #     )

    return {
        "target_hours_per_volume": 4.24,
    }


def show_main_content(settings: dict, data: data.ProcessedData):
    """
    Render main content of the app, given the user options from the side bar and pre-processed data.
    """
    st.title("Rehabilitation Services")

    tab_1, tab_2, tab_3, tab_4 = st.tabs(
        ["KPI & Productivity", "FTE", "Data", "(Calculations)"]
    )
    s = data.stats

    with tab_1:
        st.header("KPIs")
        col_1, col_2 = st.columns(2)
        col_1.metric(
            "Revenue per Encounter",
            "$%s" % round(s["actual_revenue_per_volume"]),
            f"{s['variance_revenue_per_volume']}% {'above' if s['actual_revenue_per_volume'] >= s['target_revenue_per_volume'] else 'below'} target",
        )
        col_2.metric(
            "Target Revenue per Encounter",
            f"${round(s['target_revenue_per_volume'])}",
        )

        col_1, col_2 = st.columns(2)
        col_1.metric(
            "Expense per Encounter",
            "$%s" % round(s["actual_expense_per_volume"]),
            delta=f"{s['variance_expense_per_volume']}% {'above' if s['actual_expense_per_volume'] >= s['target_expense_per_volume'] else 'below'} target",
            delta_color="inverse",
        )
        col_2.metric(
            "Target Expense per Encounter",
            f"${round(s['target_expense_per_volume'])}",
        )

        st.header("Productivity")
        col_1, col_2 = st.columns(2)
        col_1.metric("Hours per Encounter", round(s["actual_hours_per_volume"], 2))
        col_1.metric("Target Hours per Encounter", s["target_hours_per_volume"])
        col_1.metric("FTE Variance", round(s["fte_variance"], 2))

        v = s["fte_variance_dollars"]
        col_2.markdown(
            "<p style='font-size:14px;'>Dollar Impact</p>"
            + f"<p style='margin-top:-15px; font-size:2rem; color:{'rgb(255, 43, 43)' if v < 0 else 'rgb(9, 171, 59)'}'>{_format_finance(v)}</p>",
            unsafe_allow_html=True,
        )

    with tab_2:
        col_1, col_2, col_3, col_4 = st.columns(4)
        col_2.metric("Hours Paid (Pay Period)", s["pay_period_hours_paid"])
        col_3.metric("YTD Hours Paid", s["ytd_hours_paid"])

        src = data.raw.fte_per_pay_period
        fig = px.bar(
            src, title="FTE per Pay Period", x="Pay Period", y="FTEs", text_auto="i"
        )
        fig.add_shape(
            type="line",
            x0=src["Pay Period"].iloc[0],
            x1=src["Pay Period"].iloc[-1],
            y0=32,
            y1=32,
            yref="y",
            xref="x",
            line=dict(color="red", width=3),
            layer="below",
        )
        st.plotly_chart(fig, use_container_width=True)

    with tab_4:
        st.write(s)

    with tab_3:
        st.header("Revenue")
        st.write(data.raw.revenue)
        st.header("Deductions")
        st.write(data.raw.deductions)
        st.header("Expenses")
        st.write(data.raw.expenses)
        st.header("Volume")
        st.write(data.raw.volume)
        st.header("Hours")
        st.write(data.raw.hours)
        st.header("Paid Hours")
        st.write(data.raw.fte_hours_paid)
        st.header("Paid FTEs")
        st.write(data.raw.fte_per_pay_period)


def _format_finance(n):
    """Return a number formatted a finance amount - dollar sign, two decimal places, commas, negative values wrapped in parens"""
    return "${0:,.2f}".format(n) if n >= 0 else "(${0:,.2f})".format(abs(n))
