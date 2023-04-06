import streamlit as st
from src import route, data_files, data, ui


def run():
    """Main streamlit app entry point"""
    # Handle routing based on query parameters
    query_params = st.experimental_get_query_params()
    route_id = route.route_by_query(query_params)

    # Render page based on the route
    if route_id == route.UPDATE:
        show_update()
    else:
        show_main()


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


def show_main():
    """
    Render the main application
    """
    # List of available source data files - eg. XLS reports from Epic, WD, etc.
    files = data_files.get()

    # Read and parse source data
    with st.spinner("Initializing..."):
        src_data = data.extract_from(files)

    # Process the source data by partitioning it and precalculating statistics
    processed_data = data.process(src_data)
    st.write(src_data.values)
    st.write(processed_data.stats)

    # Show sidebar and retrieve user specified configuration options
    settings = ui.show_settings()

    # Show main content
    ui.show_main_content(settings, processed_data)


st.set_page_config(page_title="PRH Dashboard", layout="wide")
run()
