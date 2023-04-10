import streamlit as st
from src import auth, route, data_files, data, ui


def run():
    """Main streamlit app entry point"""
    # Authenticate user
    if not auth.authenticate():
        return st.stop()

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
    if files == None or len(files) == 0:
        return st.write('No data available. Please contact administrator.')

    # Read and parse source data
    with st.spinner("Initializing..."):
        src_data = data.extract_from(files)

    # Show sidebar and retrieve user specified configuration options
    add_logo()
    settings = ui.show_settings()

    # Process the source data by partitioning it and precalculating statistics
    processed_data = data.process(settings, src_data)

    # Show main content
    ui.show_main_content(settings, processed_data)


def add_logo():
    st.markdown(
        """
        <style>
            [data-testid="stSidebar"] {
                background-image: url(https://www.pullmanregional.org/hubfs/PullmanRegionalHospital_December2019/Image/logo.svg);
                background-repeat: no-repeat;
                padding-top: 0px;
                background-position: 80px 20px;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


st.set_page_config(
    page_title="PRH Dashboard", layout="centered", initial_sidebar_state="auto"
)
run()
