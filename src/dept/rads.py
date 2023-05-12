import streamlit as st
from .. import source_data

def rads_app(src_data: source_data.RawData):
    """
    Show department specific Streamlit app
    """
    st.header('')