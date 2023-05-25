from ... import RawData
from . import data, ui, parser

def rads_page(src_data: RawData.RawData):
    """
    Show department specific Streamlit page
    """
    # Process the source data by partitioning it and precalculating statistics
    processed_data = data.process(src_data)

    # Show main content
    settings = ui.show_settings()
    ui.show(settings, processed_data)
