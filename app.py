import streamlit as st
from src import auth, route, source_data
from src.model import DB_FILE


def run():
    """Main streamlit app entry point"""
    # Fetch source data - do this before auth to ensure all requests to app cause data refresh
    # Read, parse, and cache (via @st.cache_data) source data
    with st.spinner("Initializing..."):
        src_data = source_data.from_db(DB_FILE)

    # Authenticate user
    if not auth.authenticate():
        return st.stop()

    # Handle routing based on query parameters
    query_params = st.experimental_get_query_params()
    route_id = route.route_by_query(query_params)

    # Check for access to API resources first
    if route_id == route.CLEAR_CACHE:
        # Force source_data module to reread DB from disk on next run
        return st.cache_data.clear()

    # Load source data
    if src_data is None:
        return st.write("No data available. Please contact administrator.")

    # Render page based on the route
    if route_id == route.MAIN:
        pass


st.set_page_config(
    page_title="PRH Dashboard", layout="wide", initial_sidebar_state="auto"
)
run()
