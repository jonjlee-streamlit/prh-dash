import os
import streamlit as st

BASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")

def show_page():
    """
    Retrieve list of current data files and UI to upload new files
    """
    # Allow user to upload new data files to disk
    file = _render_update_page()

    # If files were uploaded, write them to disk and update UI
    if file:
        # Ensure base data directory exists
        with open(os.path.join(BASE_PATH, file.name), "wb") as local:
            local.write(file.read())

        # Force data module to reread data from disk on next run
        st.cache_data.clear()

def _render_update_page():
    """
    Render page to allow for uploading data files
    """
    st.header("Update data files")
    st.markdown(
        '<a href="/" target="_self">Go to dashboard &gt;</a>', unsafe_allow_html=True
    )
    file = st.file_uploader("Select file to upload")
    return file
