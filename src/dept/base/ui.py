import pandas as pd
import streamlit as st
from datetime import datetime
from dateutil.relativedelta import relativedelta
from . import configs, data, figs
from ... import util, static_data
from .data import calc_income_stmt_for_month


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

        st.subheader("Sections")
        st.markdown(
            "\n".join(
                [
                    "* [KPIs](#kpis)",
                    "* [Volumes](#volumes)",
                    "* [Hours/FTE](#hours)",
                    "* [Income Statment](#income)",
                ]
            )
        )

    return {"dept_id": dept_id, "dept_name": dept_id_to_name(dept_id)}


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

    # Title with department name and sub-department. e.g. "Imaging - CT"
    if len(config.wd_ids) > 1:
        st.title(f"{config.name} · {settings['dept_name']}")
    else:
        st.title(f"{config.name}")

    # Main content
    st.header("Key Performance Indicators", anchor="kpis", divider="gray")
    _show_kpi(settings, data)
    st.header("Volumes", anchor="volumes", divider="gray")
    _show_volumes(settings, data)
    st.header("Hours and FTE", anchor="hours", divider="gray")
    _show_hours(settings, data)
    st.header("Income Statement", anchor="income", divider="gray")
    _show_income_stmt(settings, data)


def _show_kpi(settings: dict, data: data.DeptData):
    s = data.stats

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


def _show_volumes(settings: dict, data: data.DeptData):
    last_month = datetime.strftime(datetime.today() - relativedelta(months=1), "%b %Y")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric(f"Last Month ({last_month})", data.stats["last_month_volume"])
    col2.metric(f"Year to Date", data.stats["ytd_volume"])

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
        df = _filter_by_period(data.volumes, volumes_period)
        figs.volumes_fig(df)


def _show_hours(settings: dict, data: data.DeptData):
    if data.hours is None or data.hours.shape[0] == 0:
        return st.write("No data for this month")

    # Show productive / non-productive hours for month
    st.subheader("Summary")
    figs.hours_table(
        data.latest_pay_period, data.hours_latest_pay_period, data.hours_ytd
    )

    # Show graph of historical FTE. Allow user to select how many months to show.
    st.write("&nbsp;")
    st.subheader("By Pay Period")

    # Select the pay period number
    fte_period = st.selectbox(
        key="fte_period",
        label="Pay Period",
        label_visibility="collapsed",
        options=["Year to Date", "2 Years", "5 Years", "All Pay Periods"]
    )

    col1, col2 = st.columns(2)
    df = _filter_pay_periods_by_desc(data.hours, fte_period)
    with col1:
        figs.fte_fig(df, data.stats["budget_fte"])
    with col2:
        figs.hours_fig(df)


def _show_income_stmt(settings: dict, data: data.DeptData):
    month = st.selectbox(
        label="Month",
        label_visibility="hidden",
        options=data.avail_income_stmt_months,
        format_func=lambda m: datetime.strptime(m, "%Y-%m").strftime("%b %Y"),
    )

    income_stmt = calc_income_stmt_for_month(data.income_stmt, month)

    figs.aggrid_income_stmt(income_stmt, month)


def _filter_by_period(df, period_str, col="month"):
    """
    Return data from the dataframe, df, with dates within the period_str, like "12 Months".
    Filter df based on the column specified by col, which should be string formatted as "YYYY-MM"
    """
    # Filter based on first and last date. Treat None values as no filter.
    first_month, last_month = util.period_str_to_month_strs(period_str)
    if first_month:
        df = df[df.loc[:, col] >= first_month]
    if last_month:
        df = df[df.loc[:, col] <= last_month]
    return df

def _filter_pay_periods_by_desc(df, period_str):
    if period_str == "All Pay Periods":
        return df
    if period_str == "Year to Date":
        return df[df["pay_period"] >= f"{datetime.today().year}-01"]
    if period_str == "2 Years":
        return df[df["pay_period"] >= f"{datetime.today().year-1}-01"]
    if period_str == "5 Years":
        return df[df["pay_period"] >= f"{datetime.today().year-4}-01"]
