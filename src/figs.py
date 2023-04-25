import pandas as pd
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
    # Build grouping column based on row_groups
    row_groups = [
        (1, 3),
        (4, 7),
        (12, 19),
        (23, 27),
        (28, 52),
        (53, 59),
        (60, 70),
        (71, 74),
        (75, 83),
        (84, 87),
        (90, 103),
        (104, 105),
    ]
    df["hier"] = _hierarchy_from_row_groups(row_groups, len(df.index))

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
                if ({ str(bold_rows) }.includes(params.data['Ledger Account'])) {{
                    console.log(params);
                    return {{'font-weight': 'bold'}}
                }}
            }}
            """
        ),
        # Row grouping
        autoGroupColumnDef=dict(
            # Don't show a column name
            headerName="",
            maxWidth=40,
            # Don't add suffice with count of grouped up rows - eg. "> Supplies (10)"
            # And innerRenderer() returning null results in blank text for grouped rows
            cellRendererParams=dict(
                suppressCount=True, innerRenderer=JsCode("function() {}")
            ),
            # For grouped rows (those that have a hier value with a /), use the
            # default rendere agGroupCellRenderer, which will show the toggle button
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
                    if (params.value && !params.value.indexOf('/')) {
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
        getDataPath=JsCode("function(data) { return data.hier.split('/'); }"),
        animateRows=True,
        # groupDefaultExpanded=-1,
    )
    # gb.configure_column("i", headerName="Row", valueGetter="node.rowIndex", pinned="left", width=30)
    gb.configure_column("hier", hide=True)

    # Configure decimals, commas, etc when displaying of money and percent columns
    gb.configure_columns(
        [
            "Actual (Month)",
            "Budget (Month)",
            "Variance (Month)",
            "Actual (Year)",
            "Budget (Year)",
            "Variance (Year)",
        ],
        type=["numericColumn", "numberColumnFilter", "customNumericFormat"],
        valueFormatter=JsCode(
            "function(params) { return (params.value == null) ? params.value : params.value.toLocaleString('en-US', { maximumFractionDigits:2 }) }"
        ),
    )
    gb.configure_columns(
        [
            "Variance % (Month)",
            "Variance % (Year)",
        ],
        type=["numericColumn", "numberColumnFilter", "customNumericFormat"],
        valueFormatter=JsCode(
            "function(params) { return (params.value == null) ? params.value : (params.value < 0 ? '(' + Math.abs(Math.round(params.value * 100)) + '%)' : Math.round(params.value * 100) + '%') }"
        ),
    )

    # Finally show data table
    AgGrid(
        df,
        gridOptions=gb.build(),
        # columns_auto_size_mode=ColumnsAutoSizeMode.FIT_CONTENTS,
        allow_unsafe_jscode=True,
    )


def _hierarchy_from_row_groups(groups, len):
    """
    Given a list of row groups as tuples: [(a,b), (c,d), ...], returns a new list with elements formatted
    to provide a hierarchy grouping rows as specified. Elements not in any row group are represented by their
    index. Elements in a one or more row group have their parent index, /, then the element index.
    """
    res = [str(i) for i in range(0, len)]
    for i in range(0, len):
        prefix = ""
        for group_start, group_end in groups:
            if group_start < i and group_end >= i:
                prefix = f"{prefix}{group_start}/"
                res[i] = prefix + res[i]

    return res
