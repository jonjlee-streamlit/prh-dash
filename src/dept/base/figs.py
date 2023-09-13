import pandas as pd
import plotly.express as px
import streamlit as st
from datetime import datetime
from st_aggrid import AgGrid, GridOptionsBuilder, ColumnsAutoSizeMode, JsCode


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


def volumes_fig(df):
    df = df.copy()
    df.columns = ["Month", "Volume"]
    fig = px.bar(
        df,
        x=df.columns[0],
        y=df.columns[1],
        text=df.columns[1],
    )
    fig.update_traces(
        hovertemplate="<br>".join(
            [
                "%{x|%b %Y}",
                "%{y} exams",
            ]
        ),
        texttemplate="%{text:,}",
    )
    # Remove excessive top margin
    fig.update_layout(
        margin={"t": 0},
        hovermode="x",
        xaxis_title=None,
        yaxis_title=None,
    )
    st.plotly_chart(fig, use_container_width=True)


def hours_table(month, hours_for_month, hours_ytd):
    # Combine hours for month and YTD hours into single table
    # Transpose to so the numbers appear in columns
    df = pd.DataFrame([hours_for_month, hours_ytd]).T.reset_index()

    # Convert month from format "2023-01" to "Jan 2023"
    month = datetime.strptime(month, "%Y-%m").strftime("%b %Y")
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

    # Create borders and row bolding
    left_margin = 25
    styled_df = (
        df.style.hide(axis=0)
        .format("{:,.0f}", subset=df.columns[1:].tolist())
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


def fte_fig(src, budget_fte):
    df = src[["month", "total_fte"]].copy()
    df = df.sort_values(by=["month"], ascending=[True])
    df.columns = ["Month", "FTE"]
    fig = px.bar(
        df, x=df.columns[0], y=df.columns[1], text=df.columns[1], text_auto=".1f"
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
    # On hover text, show pay period number "2023 PP#1" and round y value to 1 decimal
    fig.update_traces(hovertemplate="%{y:.1f} FTE", texttemplate="%{text:,.0f}")
    fig.update_layout(
        margin={"t": 25},
        hovermode="x unified",
        xaxis={"tickformat": "%b %Y"},
        xaxis_title=None,
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
