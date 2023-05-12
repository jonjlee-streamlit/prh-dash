import streamlit as st
from . import data_files

def show_page():
    """
    Retrieve list of current data files and UI to upload new files
    """
    # Allow user to upload new data files to disk
    cur_files = data_files.get_on_disk()
    files, remove_existing = _render_update_page(cur_files)

    # If files were uploaded, write them to disk and update UI
    if files and len(files) > 0:
        data_files.update_on_disk(files, remove_existing)

        # Force data module to reread data from disk on next run
        st.cache_data.clear()

def _render_update_page(cur_files: list[str]) -> tuple[list | None, bool]:
    """
    Render page to allow for uploading data files
    """
    st.header("Update data files")
    st.markdown(
        '<a href="/" target="_self">Go to dashboard &gt;</a>', unsafe_allow_html=True
    )
    if cur_files:
        st.write("Current data files:")
        st.write(cur_files)
    remove_existing = st.checkbox("Remove existing files before upload")
    files = st.file_uploader("Select files to upload", accept_multiple_files=True)
    return files, remove_existing
