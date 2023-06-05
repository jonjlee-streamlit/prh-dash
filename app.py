import streamlit as st
from src import auth, route, data_files, source_data, update
from src.dept import rads_page, therapy_page


def run():
    """Main streamlit app entry point"""
    # Authenticate user
    if not auth.authenticate():
        return st.stop()

    # Handle routing based on query parameters
    query_params = st.experimental_get_query_params()
    route_id = route.route_by_query(query_params)

    # For updating data, show update page and stop before loading data
    if route_id == route.UPDATE:
        return update.show_page()

    # Load source data
    src_data = load_data()
    if src_data is None:
        return st.write("No data available. Please contact administrator.")

    # Render page based on the route
    if route_id == route.MAIN:
        therapy_page(src_data)
    elif route_id == route.RADS:
        rads_page(src_data)


def load_data():
    """
    Reads and caches all source data files
    """
    # List of available source data files - eg. XLS reports from Epic, WD, etc.
    files = data_files.get()
    if files == None or len(files) == 0:
        return None

    # Read, parse, and cache (via @st.cache_data) source data
    with st.spinner("Initializing..."):
        return source_data.extract_from(files)


st.set_page_config(
    page_title="PRH Dashboard", layout="centered", initial_sidebar_state="auto"
)
run()
