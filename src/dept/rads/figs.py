import streamlit as st
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
