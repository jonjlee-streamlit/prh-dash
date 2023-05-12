import streamlit as st
from src import auth, route, data_files, data, ui, util
from src.dept import rads_app, therapy_app

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
        return show_update()

    # Load source data
    src_data = load_data()
    if src_data is None:
        return st.write("No data available. Please contact administrator.")

    # Render page based on the route
    if route_id == route.MAIN:     
        therapy_app(src_data)
    elif route_id == route.RADS:
        rads_app(src_data)


def show_update():
    """
    Render page to allow for uploading data files
    """
    # Allow user to upload new data files to disk
    cur_files = data_files.get_on_disk()
    files, remove_existing = ui.show_update(cur_files)

    # If files were uploaded, write them to disk and update UI
    if files and len(files) > 0:
        data_files.update_on_disk(files, remove_existing)

        # Force data module to reread data from disk on next run
        st.cache_data.clear()


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
        return data.extract_from(files)


def show_main(src_data):
    """
    Render the default page
    """
    # Show sidebar and retrieve user specified configuration options
    util.st_prh_logo()
    settings = ui.show_settings()

    # Process the source data by partitioning it and precalculating statistics
    processed_data = data.process(settings, src_data)

    # Show main content
    ui.show_main_content(settings, processed_data)


st.set_page_config(
    page_title="PRH Dashboard", layout="centered", initial_sidebar_state="auto"
)
run()
