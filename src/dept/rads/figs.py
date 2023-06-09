import pandas as pd
import streamlit as st
import plotly.express as px
from ... import util
from st_aggrid import AgGrid, GridOptionsBuilder, ColumnsAutoSizeMode, JsCode


def aggrid_income_stmt(df):
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

    # Configure decimals, commas, etc when displaying of money and percent columns
    gb.configure_columns(
        [
            "Actual",
            "Budget",
        ],
        type=["numericColumn", "numberColumnFilter", "customNumericFormat"],
        aggFunc="sum",
        valueFormatter=JsCode(
            "function(params) { return (params.value == null) ? params.value : params.value.toLocaleString('en-US', { maximumFractionDigits:2 }) }"
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
        )
    )
    # Remove excessive top margin
    fig.update_layout(
        margin={"t": 0},
    )
    st.plotly_chart(fig, use_container_width=True)


def hours_table(hours_for_month, hours_ytd):
    # Combine hours for month and YTD hours into single table
    # Transpose to so the numbers appear in columns
    df = pd.concat([hours_for_month, hours_ytd]).T.reset_index()
    # Use the original row labels ("Jan 2023", "YTD") as column headers, and drop the row
    df.columns = df.iloc[0, :]
    df = df.iloc[1:, :]

    # Create borders and row bolding
    left_margin = 25
    styled_df = (
        df.style.hide(axis=0)
        .format("{:.1f}", subset=df.columns[1:].tolist())
        .set_table_styles(
            [
                {"selector": "", "props": [("margin-left", str(left_margin) + "px")]},
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
                    "selector": "tr:last-child, tr:nth-last-child(2)",
                    "props": [("font-weight", "bold")],
                },
            ]
        )
    )
    st.markdown(styled_df.to_html(), unsafe_allow_html=True)


def fte_fig(src, budget_fte):
    df = src[["month", "fte"]]
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
        align="left",
        xshift=150,
        yshift=15,
    )
    # Show months on x axis like "Jan 2023"
    fig.update_xaxes(tickformat="%b %Y")
    # On hover text, show month "Jan 2023" and round y value to 1 decimal
    fig.update_traces(
        hovertemplate="<br>".join(
            [
                "%{x|%b %Y}",
                "%{y:.1f} FTE",
            ]
        )
    )
    # Remove excessive top margin
    fig.update_layout(
        margin={"t": 0},
    )
    st.plotly_chart(fig, use_container_width=True)


def hours_fig(src):
    df = src[["month", "productive", "nonproductive"]]
    df.columns = ["Month", "Productive", "Non-productive"]
    fig = px.bar(
        df,
        x=df.columns[0],
        y=[df.columns[1], df.columns[2]],
        text_auto=".1f",
    )
    fig.update_yaxes(title_text="Hours")
    fig.update_layout(legend_title_text="")
    # Remove excessive top margin
    fig.update_layout(
        margin={"t": 0},
    )
    st.plotly_chart(fig, use_container_width=True)
