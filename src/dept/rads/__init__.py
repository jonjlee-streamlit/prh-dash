from ... import source_data
from . import data, ui

def rads_page(src_data: source_data.RawData):
    """
    Show department specific Streamlit page
    """
    # Process the source data by partitioning it and precalculating statistics
    processed_data = data.process(src_data)

    # Show main content
    ui.show(processed_data)
