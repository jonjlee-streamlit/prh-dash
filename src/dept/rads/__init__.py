from ... import RawData
from . import data, ui, parser


def rads_page(src_data: RawData.RawData):
    """
    Show department specific Streamlit page
    """
    # Get user settings
    settings = ui.show_settings()

    # Process the source data by partitioning it and precalculating statistics
    processed_data = data.process(settings, src_data)

    # Show main content
    ui.show(settings, processed_data)
