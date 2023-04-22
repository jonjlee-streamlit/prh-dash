import pandas as pd
import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode


def table_with_groups(data, row_groups):
    # Build grouping column based on row_groups
    hier = _hierarchy_from_row_groups(row_groups)
    data = {
        "hier": [
            "1",
            "B",
            "B/3",
            "4",
            "D",
            "D/6",
            "D/7",
        ],
        "Column1": [1, 2, 3, 4, 5, 6, 7],
        "Column2": [10, 20, 30, 40, 50, 60, 70],
    }
    df = pd.DataFrame(data)
    st.write(df)
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_grid_options(
        autoGroupColumnDef=dict(
            headerName="",
            maxWidth=40,
            cellRendererParams=dict(
                suppressCount=True, innerRenderer=JsCode("function() {}")
            ),
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
        )
    )
    gridOptions = gb.build()

    gridOptions["columnDefs"] = [
        {"field": "Column1"},
        {"field": "Column2"},
    ]
    gridOptions["treeData"] = True
    gridOptions["animateRows"] = True
    gridOptions["getDataPath"] = JsCode(
        "function(data) { return data.hier.split('/') }"
    ).js_code

    AgGrid(df, gridOptions=gridOptions, allow_unsafe_jscode=True)


def _hierarchy_from_row_groups(row_groups):
    """
    Given a list of non-overlapping row groups as tuples: [(a,b), (c,d), ...], returns a new list with elements formatted
    to provide a hierarchy grouping rows as specified. Elements not in any row group are represented by their index, while
    elements in a row group have an incrementing letter / the element index.
    """
    hierarchy = []
    letter = ord("A")
    idx = 0

    for start, end in row_groups:
        # Add elements before the range
        while idx < start:
            hierarchy.append(idx)
            idx += 1

        # Add elements in the range
        while idx <= end:
            if idx == start:
                hierarchy.append(chr(letter))
            else:
                hierarchy.append(f"{chr(letter)}/{idx}")
            idx += 1

        # Increment the letter for the next range
        letter += 1

    # Add remaining elements after the last range
    while idx < end + 1:
        hierarchy.append(idx)
        idx += 1

    return hierarchy
