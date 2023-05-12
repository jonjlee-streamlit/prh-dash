import streamlit as st

# IDs for defined routes
MAIN = "main"
UPDATE = "update"
RADS = "rads"
DEPTS = (RADS)

def route_by_query(query_params: dict) -> str:
    """
    Returns a route ID given the query parameters in the URL.
    Expects query_params to be in the format { "param": ["value 1", "value 2" ] }, corresponding to Streamlit docs:
    https://docs.streamlit.io/library/api-reference/utilities/st.experimental_get_query_params
    """
    dept = query_params.get("d")
    if query_params.get("update") == ["1"]:
        return UPDATE
    elif dept and len(dept) > 0 and dept[0] in DEPTS:
        return dept[0]

    return MAIN
