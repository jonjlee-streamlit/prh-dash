"""
This module contains functions to render various parts of the application, including the auth screen, 
sidebar for configuration options, main app content, etc.
"""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from st_aggrid import AgGrid, GridOptionsBuilder
from .data import ProcessedData
from . import fte_calc
from . import figs


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


def show_main_content(settings: dict, data: ProcessedData):
    """
    Render main content of the app, given the user options from the side bar and pre-processed data.
    """
    st.title("Rehabilitation Services")

    tab_kpis, tab_income_stmt, tab_fte, tab_fte_calc = st.tabs(
        ["KPI & Productivity", "Income Statement", "FTE", "Staffing Calculator"]
    )
    s = data.stats

    with tab_kpis:
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

    with tab_income_stmt:
        figs.aggrid_income_stmt(data.raw.income_statement)

    with tab_fte:
        styled_df = (
            data.raw.fte_hours_paid.style.hide(axis=0)
            .format("{:.2f}", subset=["Current Pay Period", "YTD"])
            .set_table_styles(
                [
                    {"selector": "", "props": [("margin-left", "200px")]},
                    {"selector": "tr", "props": [("border-top", "0px")]},
                    {"selector": "th, td", "props": [("border", "0px")]},
                    {"selector": "td", "props": [("padding", "3px 13px")]},
                    {
                        "selector": "td:nth-child(2), td:nth-child(3)",
                        "props": [("border-bottom", "1px solid black")],
                    },
                    {
                        "selector": "tr:last-child td:nth-child(2), tr:last-child td:nth-child(3)",
                        "props": [("border-bottom", "2px solid black")],
                    },
                    {
                        "selector": "tr:last-child",
                        "props": [("font-weight", "bold")],
                    },
                ]
            )
        )
        st.markdown(styled_df.to_html(), unsafe_allow_html=True)
        # col_2.metric("Hours Paid (Pay Period)", s["pay_period_hours_paid"])
        # col_3.metric("YTD Hours Paid", s["ytd_hours_paid"])

        src = data.raw.fte_per_pay_period
        fig = px.bar(src, x="Pay Period", y="FTEs", text_auto="i")
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
        fig.add_annotation(
            x=src["Pay Period"].iloc[-1],
            y=32,
            xref="x",
            yref="y",
            text="Budget: 32.0",
            showarrow=False,
            font=dict(size=14, color="red"),
            align="left",
            xshift=-30,
            yshift=-15,
        )
        st.plotly_chart(fig, use_container_width=True)

    with tab_fte_calc:
        st.subheader("FTE Calculator")
        fte_requested = st.number_input(
            "FTE Requested", min_value=0.25, max_value=100.0, value=33.0, step=0.25
        )
        fte_results = fte_calc.calc(fte_requested)

        st.markdown(
            f"""
            <center>
            <table style="width: 100%; margin-bottom: 25px;">
                <tr>
                    <td style="width: 100px; text-align: center;">{'{0:,.0f}'.format(fte_results.productive_hours_needed_for_volume)}</td>
                    <td>Productive man-hours needed for projected volume</td>
                </tr>
                <tr>
                    <td style="text-align: center; font-weight: bold; background: #ffff00;">{'{0:,.0f}'.format(fte_results.standard_volume)}</td>
                    <td>Standard Volume</td>
                </tr>
            </table>
            </center>
            """,
            unsafe_allow_html=True,
        )

        col_1, col_2 = st.columns(2)
        col_1.metric("Statistical Impact", round(fte_results.statistical_impact_volume))
        col_2.metric(
            "Salary/Wage Impact", _format_finance(fte_results.salary_impact_dollars)
        )
        col_1.metric(
            "Reimbursement", _format_finance(fte_results.reimbursement_dollars)
        )
        col_2.metric(
            "Total Net Gain/Loss", _format_finance(fte_results.net_impact_dollars)
        )


def _format_finance(n):
    """Return a number formatted a finance amount - dollar sign, two decimal places, commas, negative values wrapped in parens"""
    return "${0:,.2f}".format(n) if n >= 0 else "(${0:,.2f})".format(abs(n))
