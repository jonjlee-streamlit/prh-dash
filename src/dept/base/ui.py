import pandas as pd
import streamlit as st
from datetime import datetime
from dateutil.relativedelta import relativedelta
from . import configs, data, figs
from ... import util, static_data, source_data


def show_settings(config: configs.DeptConfig, src_data: source_data.SourceData) -> dict:
    """
    Render the sidebar and return the dict with configuration options set by the user.
    """
    with st.sidebar:
        util.st_sidebar_prh_logo()

        if len(config.wd_ids) > 1:
            dept_id = st.selectbox(
                "Department",
                options=["All"] + config.wd_ids,
                format_func=_dept_name,
            )
        else:
            dept_id = config.wd_ids[0]

        # Get the minimum and maximum months in the data
        min_month = min(
            src_data.volumes_df["month"].min(),
            src_data.hours_df["month"].min(),
            src_data.income_stmt_df["month"].min(),
        )
        max_month = min(
            src_data.volumes_df["month"].max(),
            src_data.hours_df["month"].max(),
            src_data.income_stmt_df["month"].max(),
        )
        month = st.selectbox(
            label="Month",
            options=_enumerate_months(min_month, max_month),
            format_func=lambda m: datetime.strptime(m, "%Y-%m").strftime("%b %Y"),
        )

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

    return {"dept_id": dept_id, "month": month}


def show(config: configs.DeptConfig, settings: dict, data: data.DeptData):
    """
    Render main content for department
    """
    s = data.stats

    # Title with department name and sub-department. e.g. "Imaging - CT"
    if len(config.wd_ids) > 1:
        st.title(f"{config.name} · {_dept_name(settings['dept_id'])}")
    else:
        st.title(f"{config.name}")

    # Main content
    kpi_month_str = datetime.strptime(s["kpi_month_max"], "%Y-%m").strftime("%b %Y")
    st.header(
        f"Key Performance Indicators, Year to {kpi_month_str}",
        anchor="kpis",
        divider="gray",
    )
    _show_kpi(settings, data)
    st.header("Volumes", anchor="volumes", divider="gray")
    _show_volumes(settings, data)
    st.header("Hours and FTE", anchor="hours", divider="gray")
    _show_hours(settings, data)
    month_str = datetime.strptime(settings["month"], "%Y-%m").strftime("%b %Y")
    st.header(f"Income Statement - {month_str}", anchor="income", divider="gray")
    _show_income_stmt(settings, data)


def _show_kpi(settings: dict, data: data.DeptData):
    s = data.stats

    if all(
        s == 0
        for s in [
            s["revenue_per_volume"],
            s["target_revenue_per_volume"],
            s["expense_per_volume"],
            s["target_expense_per_volume"],
            s["hours_per_volume"],
            s["fte_variance"],
        ]
    ):
        return st.write("No data for department")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric(
        "Revenue per Exam",
        f"${s['revenue_per_volume']:,.0f}",
        f"{s['variance_revenue_per_volume']}% {'above' if s['revenue_per_volume'] >= s['target_revenue_per_volume'] else 'below'} target",
    )
    col2.metric(
        "Target Revenue per Exam",
        f"${s['target_revenue_per_volume']:,.0f}",
    )

    col1, col2, col3, col4 = st.columns(4)
    col1.metric(
        "Expense per Exam",
        f"${s['expense_per_volume']:,.0f}",
        delta=f"{s['variance_expense_per_volume']}% {'above' if s['expense_per_volume'] >= s['target_expense_per_volume'] else 'below'} target",
        delta_color="inverse",
    )
    col2.metric(
        "Target Expense per Exam",
        f"${s['target_expense_per_volume']:,.0f}",
    )

    st.subheader("Productivity")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Hours per Exam", round(s["hours_per_volume"], 2))
    col2.metric("Target Hours per Exam", round(s["target_hours_per_volume"], 2))
    col1.metric("FTE Variance", round(s["fte_variance"], 2))

    v = round(s["fte_variance_dollars"])
    color = "rgb(255, 43, 43)" if v < 0 else "rgb(9, 171, 59)"
    col2.markdown(
        "<p style='font-size:14px;'>Dollar Impact</p>"
        + f"<p style='margin-top:-15px; font-size:2rem; color:{color}'>{util.format_finance(v)}</p>",
        unsafe_allow_html=True,
    )


def _show_volumes(settings: dict, data: data.DeptData):

    if all(
        s == 0
        for s in [
            data.stats["month_volume"],
            data.stats["month_budget_volume"],
            data.stats["ytm_volume"],
            data.stats["ytm_budget_volume"],
        ]
    ):
        return st.write("No data for department")

    month = datetime.strptime(settings["month"], "%Y-%m").strftime("%b %Y")

    st.subheader("Summary")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric(f"Month ({month})", f"{data.stats['month_volume']:,}")
    col2.metric(f"Target for Month", f"{data.stats['month_budget_volume']:,.0f}")
    col1.metric(f"Year to {month}", f"{data.stats['ytm_volume']:,}")
    col2.metric(
        f"Target for Year to {month}", f"{data.stats['ytm_budget_volume']:,.0f}"
    )

    # Show graph of historical volumes. Allow user to select how many months to show.
    st.subheader("Volumes by Month")
    col_graph, col_period = st.columns((13, 3))
    with col_period:
        volumes_period = st.selectbox(
            label="Show",
            key="volume_period",
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
    figs.hours_table(data.month, data.hours_for_month, data.hours_ytm)

    # Show graph of historical FTE. Allow user to select how many months to show.
    st.write("&nbsp;")
    st.subheader("By Month")

    # Select the amount of historical data to display in months
    col1, col2, col_period = st.columns((7, 7, 3))
    with col_period:
        sel_period = st.selectbox(
            label="Show",
            key="hours_period",
            label_visibility="collapsed",
            options=["12 Months", "24 Months", "5 Years", "All"],
        )

    df = _filter_by_period(data.hours, sel_period)
    with col1:
        figs.fte_fig(df, data.stats["budget_fte"])
    with col2:
        figs.hours_fig(df)


def _show_income_stmt(settings: dict, data: data.DeptData):
    figs.aggrid_income_stmt(data.income_stmt, settings["month"])


def _dept_name(key):
    if key == "All":
        return key
    if hasattr(key, "name"):
        return key.name
    return static_data.WDID_TO_DEPT_NAME.get(key, f"Unknown Department {key}")


def _enumerate_months(min_month, max_month):
    min_month = datetime.strptime(min_month, "%Y-%m")
    cur_month = datetime.strptime(max_month, "%Y-%m")
    months = []
    while cur_month >= min_month:
        months.append(cur_month.strftime("%Y-%m"))
        cur_month += relativedelta(months=-1)
    return months


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
