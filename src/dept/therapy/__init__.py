import streamlit as st

from . import data, ui

def therapy_page(src_data):
    """
    Show department specific Streamlit page
    """
    # Show sidebar and retrieve user specified configuration options
    settings = ui.show_settings()

    # Process the source data by partitioning it and precalculating statistics
    processed_data = data.process(settings, src_data)

    # Show main content
    ui.show(settings, processed_data)
