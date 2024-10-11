import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from datetime import datetime
from st_aggrid import AgGrid, GridOptionsBuilder, ColumnsAutoSizeMode, JsCode
from ... import util


# Display a gauge chart with 0% variance in the middle
def kpi_gauge(title, variance_pct, yellow_threshold, red_threshold, gauge_max, key=None):
    color = "#238823"
    textcolor = color
    if abs(variance_pct) >= red_threshold:
        color = "#EF553B"
        textcolor = color
    elif abs(variance_pct) >= yellow_threshold:
        color = "#FFBF00"
        textcolor = "#b38600"

    arrow = "&#9650; " if variance_pct > 0 else "&#9660; " if variance_pct < 0 else ""

    fig = go.Figure(
        go.Indicator(
            # title={"text": title, "font": {"size": 14, "color": "#000000"}},
            mode="gauge",
            value=variance_pct,
            number={"suffix": "%"},
            gauge={
                "bar": {"thickness": 0},
                "axis": {
                    "range": [-gauge_max, gauge_max],
                    "showticklabels": False,
                    "ticklen": 0,
                    "tickvals": [
                        -red_threshold,
                        -yellow_threshold,
                        0,
                        yellow_threshold,
                        red_threshold,
                    ],
                    "ticksuffix": "%",
                },
                "steps": [
                    {
                        "range": [0, variance_pct],
                        "color": color,
                        "thickness": 1,
                    },
                ],
                "threshold": {
                    "line": {"color": color},
                    "thickness": 1 if variance_pct == 0 else 0,
                    "value": variance_pct,
                },
            },
        )
    )
    fig.add_annotation(
        text=f"{arrow}{variance_pct}% {'above' if variance_pct >= 0 else 'below'} target",
        xanchor="center",
        y=-0.7,
        showarrow=False,
        font={"size": 16, "color": textcolor},
    )
    fig.update_layout(
        dict(
            showlegend=False,
            margin=dict(autoexpand=False, b=50, t=10, pad=0),
            height=100,
        )
    )
    st.plotly_chart(fig, use_container_width=True, key=key)


def aggrid_income_stmt(df, month=None):
    # Bold these Ledger Account rows
    bold_rows = [
        "Operating Revenues",
        "Total Revenue",
        "Net Revenue",
        "Expenses",
        "Total Operating Expenses",
        "Operating Margin",
        "Contribution Margin",
    ]

    # Update YTD column headers for the specific month
    if month:
        # Convert month from format "2023-01" to "Jan 2023"
        month = datetime.strptime(month, "%Y-%m").strftime("%b %Y")
        df.columns.values[-2] = f"Actual, Year to {month}"
        df.columns.values[-1] = f"Budget, Year to {month}"

    # Create AgGrid display configuration to do row grouping and bolding
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_grid_options(
        # Auto-size columns, based width on content, not header
        skipHeaderOnAutoSize=True,
        suppressColumnVirtualisation=True,
        # Bold columns based on contents of the Legder Account column
        getRowStyle=JsCode(
            f"""
              function(params) {{
                  if ({ str(bold_rows) }.includes(params?.data?.['Ledger Account'])) {{
                      return {{'font-weight': 'bold'}}
                  }}
              }}
              """
        ),
        # Row grouping
        autoGroupColumnDef=dict(
            # Don't show a column name
            headerName="",
            maxWidth=90,
            # Don't add suffice with count of grouped up rows - eg. "> Supplies (10)"
            # And innerRenderer() returning null results in blank text for grouped rows
            cellRendererParams=dict(
                suppressCount=True, innerRenderer=JsCode("function() {}")
            ),
            # For grouped rows (those that have a hier value with a |), use the
            # default renderer agGroupCellRenderer, which will show the toggle button
            # and call innerRenderer to determine the text to show.
            #
            # For non-grouped rows, just return an empty <span> so no text is shown.
            cellRendererSelector=JsCode(
                """
                function(params) {
                    class EmptyRenderer {
                        getGui() { return document.createElement('span') }
                        refresh() { return true; }
                    }
                    if (params.value && !params.value.indexOf('|')) {
                        return null
                    } else {
                        return {
                            component: 'agGroupCellRenderer',
                        };
                    }
                }
                """,
            ),
        ),
        # Row grouping is actually using AgGrid Tree Data mode. See _hierarchy_from_row_groups() for
        # how the tree paths are generated.
        treeData=True,
        getDataPath=JsCode("function(data) { return data.hier.split('|'); }"),
        animateRows=True,
        groupDefaultExpanded=1,
    )
    # gb.configure_column("i", headerName="Row", valueGetter="node.rowIndex", pinned="left", width=30)
    gb.configure_column("hier", hide=True)
    gb.configure_column("Month", hide=True)

    # Configure decimals, commas, etc when displaying of money and percent columns, which are the last 4 columns of the dataframe:
    # Actual, Budget, Actual Year to MM/YYYY, Budget Year to MM/YYYY
    gb.configure_columns(
        df.columns[-4:],
        type=["numericColumn", "numberColumnFilter", "customNumericFormat"],
        aggFunc="sum",
        valueFormatter=JsCode(
            "function(params) { return (params.value == null) ? params.value : params.value.toLocaleString('en-US', {style:'currency', currency:'USD', currencySign: 'accounting', maximumFractionDigits: 0}) }"
        ),
    )

    # Finally show data table
    AgGrid(
        df,
        height=810,
        gridOptions=gb.build(),
        # columns_auto_size_mode=ColumnsAutoSizeMode.FIT_CONTENTS,
        allow_unsafe_jscode=True,
    )
    # Work around to ensure that AgGrid height doesn't collapse when in non-active tab after user interactions
    st.markdown(
        """
        <style>
            .element-container iframe {
                min-height: 810px;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def volumes_fig(src, group_by_month):
    if group_by_month:
        # Groups data by month, show a bar for each year above each month
        df = util.group_data_by_month(src, month_col="month", value_col="volume")
        df.columns = ["Month", "Volume", "Year"]
        color = "Year"
    else:
        # Display as normal time series data
        df = src.copy()
        df = df.rename(columns={"month": "Month", "volume": "Volume"})
        color = None

    fig = px.bar(df, x="Month", y="Volume", text="Volume", color=color, barmode="group")
    fig.update_traces(
        hovertemplate="%{y} exams",
        texttemplate="%{text:,}",
    )
    # Remove excessive top margin
    fig.update_layout(
        margin={"t": 0},
        hovermode="x unified",
        xaxis_title=None,
        yaxis_title=None,
    )
    st.plotly_chart(fig, use_container_width=True)


def hours_table(month, hours_for_month, hours_ytd):
    # Combine hours for month and YTD hours into single table
    # Transpose to so the numbers appear in columns
    df = pd.DataFrame([hours_for_month, hours_ytd]).T.reset_index()

    # Convert month from format "2023-01" to "Jan 2023"
    month = util.YYYY_MM_to_month_str(month)
    df.columns = ["", f"Month ({month})", f"Year to {month}"]

    # Assign row headers
    df.loc[:, ""] = [
        "Regular Hours",
        "Overtime Hours",
        "Productive Hours",
        "Non-productive Hours",
        "Total Hours",
        "Total FTE",
    ]

    # Round all numbers in table except for the first column (labels). Last row should have 1 decimal place
    df.iloc[:-1, 1:] = df.iloc[:-1, 1:].applymap(lambda x: f"{x:.0f}")
    df.iloc[-1, 1:] = df.iloc[-1, 1:].apply(lambda x: f"{x:.1f}")

    # Create borders and row bolding
    left_margin = 25
    styled_df = (
        df.style.hide(axis=0)
        .set_table_styles(
            [
                {"selector": "", "props": [("margin-left", str(left_margin) + "px")]},
                {"selector": "tr", "props": [("border-top", "0px")]},
                {
                    "selector": "th, td",
                    "props": [("border", "0px"), ("text-align", "right")],
                },
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
                    "selector": "tr:last-child, tr:nth-last-child(2)",
                    "props": [("font-weight", "bold")],
                },
            ]
        )
    )
    st.markdown(styled_df.to_html(), unsafe_allow_html=True)


def contracted_hours_table(stats):
    # Populate data from stats into in each table cell
    df = pd.DataFrame(
        [
            ["Hours", stats["contracted_hours"], stats["prior_year_contracted_hours"]],
            [
                "Equivalent FTE",
                stats["contracted_fte"],
                stats["prior_year_contracted_fte"],
            ],
        ]
    )

    # Column headers
    contracted_hours_month = stats["contracted_hours_month"]
    prior_year_for_contracted_hours = stats["prior_year_for_contracted_hours"]
    df.columns = [
        "",
        f"Year to {contracted_hours_month}",
        f"Prior Year ({prior_year_for_contracted_hours})",
    ]

    # Create borders and row bolding
    left_margin = 25
    styled_df = (
        df.style.hide(axis=0)
        .format("{:,.1f}", subset=df.columns[1:].tolist())
        .set_table_styles(
            [
                {"selector": "", "props": [("margin-left", str(left_margin) + "px")]},
                {"selector": "tr", "props": [("border-top", "0px")]},
                {
                    "selector": "th, td",
                    "props": [("border", "0px"), ("text-align", "right")],
                },
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


def fte_fig(src, budget_fte, group_by_month):
    if group_by_month:
        # Groups data by month, show a bar for each year above each month
        df = util.group_data_by_month(src, month_col="month", value_col="total_fte")
        df.columns = ["Month", "FTE", "Year"]
        color = "Year"
    else:
        # Display as normal time series data
        df = src[["month", "total_fte"]].copy()
        df = df.sort_values(by=["month"], ascending=[True])
        df.columns = ["Month", "FTE"]
        color = None

    fig = px.bar(
        df,
        x="Month",
        y="FTE",
        color=color,
        barmode="group",
        text="FTE",
        text_auto=".1f",
    )
    # Horizontal budget line
    fig.add_hline(
        y=budget_fte + 0.05,
        line=dict(color="red", width=3),
        layer="below",
    )
    # Text for budget line. Place over last visible month and shift to the right by 80 pixels.
    fig.add_annotation(
        x=df["Month"].iloc[-1],
        y=budget_fte,
        xref="x",
        yref="y",
        text=f"Budget: {budget_fte}",
        showarrow=False,
        font=dict(size=14, color="red"),
        bgcolor="rgba(255, 255, 255, 0.94)",
        align="left",
        xshift=0,
        yshift=15,
    )
    # On hover text, round y value to 1 decimal
    fig.update_traces(hovertemplate="%{y:.1f} FTE", texttemplate="%{text:,.0f}")
    fig.update_layout(
        margin={"t": 25},
        hovermode="x unified",
        xaxis={"tickformat": "%b %Y"},
        xaxis_title=None,
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
        ),  # show legend horizontally on top right
    )
    st.plotly_chart(fig, use_container_width=True)


def hours_fig(src):
    df = src[["month", "prod_hrs", "nonprod_hrs", "total_hrs"]].copy()
    df.columns = [
        "Month",
        "Productive",
        "Non-productive",
        "Total",
    ]

    # Convert table with separate columns for prod vs non-prod to having a "Type" column
    # ie columns of [Month, Prod Hours, Nonprod Hours, Total] -> [Month, Hours, Type (Prod or Nonprod), Total]
    df = df.melt(id_vars=["Month", "Total"], var_name="Type", value_name="Hours")

    # Finally convert each row to a percent, which is what we'll actually graph
    df["Percent"] = df["Hours"] / df["Total"]

    # Stacked bar graph, one color for each unique value in Type (prod vs non-prod)
    # Also pass the actual Hours in as customdata to use in the hovertemplate
    fig = px.bar(
        df, x="Month", y="Percent", color="Type", text_auto=".1%", custom_data="Hours"
    )
    fig.update_yaxes(title_text="Hours")
    fig.update_layout(
        legend_title_text="",
        xaxis_title=None,  # Don't show x axis label
        xaxis={
            "tickformat": "%b %Y"
        },  # X value still shows up in the hover text, so format it like "Jan 2023"
        yaxis={"tickformat": ",.1%"},
        hovermode="x unified",  # Hover text based on x position of mouse, and include values of both bars
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
        ),  # show legend horizontally on top right
    )

    # On hover text, show month and round y value to 1 decimal
    fig.update_traces(
        hovertemplate="%{customdata:.1f} hours (%{y:.1%})", texttemplate="%{y:.0%}"
    )

    # Remove excessive top margin
    fig.update_layout(
        margin={"t": 25},
    )
    st.plotly_chart(fig, use_container_width=True)


def compare_hours_fig(src):
    # Show a graph with hours grouped by month across years. Don't separate prod/nonprod for this graph since that display requires
    # stacked bars and we are going to use grouped bars.
    df = util.group_data_by_month(src, month_col="month", value_col="total_hrs")
    df.columns = ["Month", "Hours", "Year"]

    fig = px.bar(
        df,
        x="Month",
        y="Hours",
        color="Year",
        barmode="group",
        text="Hours",
        text_auto=".1f",
    )

    # On hover text, show 1 decimal
    fig.update_traces(hovertemplate="%{y:.0f}h", texttemplate="%{text:,.0f}")
    fig.update_layout(
        margin={"t": 25},
        hovermode="x unified",  # Hover text based on x position of mouse, and include values of both bars
        xaxis_title=None,
        yaxis={"tickformat": ","},
        yaxis_title="Total Hours",
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
        ),  # show legend horizontally on top right
    )

    st.plotly_chart(fig, use_container_width=True)
