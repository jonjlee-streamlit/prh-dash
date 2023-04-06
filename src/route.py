import streamlit as st

# IDs for defined routes
MAIN = "main"
UPDATE = "update"


def route_by_query(query_params: dict) -> str:
    """
    Returns a route ID given the query parameters in the URL.
    Expects query_params to be in the format { "param": ["value 1", "value 2" ] }, corresponding to Streamlit docs:
    https://docs.streamlit.io/library/api-reference/utilities/st.experimental_get_query_params
    """
    if query_params.get("update") == ["1"]:
        return UPDATE

    return MAIN
