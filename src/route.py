import streamlit as st

# IDs for defined routes
MAIN = "main"
RADS = "imaging"
DEPTS = RADS

CLEAR_CACHE = "clear_cache"
API = CLEAR_CACHE


def route_by_query(query_params: dict) -> str:
    """
    Returns a route ID given the query parameters in the URL.
    Expects query_params to be in the format { "param": ["value 1", "value 2" ] }, corresponding to Streamlit docs:
    https://docs.streamlit.io/library/api-reference/utilities/st.experimental_get_query_params
    """
    dept = query_params.get("dept")
    api = query_params.get("api")
    if api and len(api) > 0 and api[0] in DEPTS:
        return api[0]
    if dept and len(dept) > 0 and dept[0] in DEPTS:
        return dept[0]

    return MAIN
