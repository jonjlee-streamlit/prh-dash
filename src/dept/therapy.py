import streamlit as st

from .therapy import data, ui
from .. import source_data, util

def therapy_app(src_data: source_data.RawData):
    """
    Show department specific Streamlit app
    """
    # Show sidebar and retrieve user specified configuration options
    util.st_prh_logo()
    settings = ui.show_settings()

    # Process the source data by partitioning it and precalculating statistics
    processed_data = data.process(settings, src_data)

    # Show main content
    ui.show(settings, processed_data)
