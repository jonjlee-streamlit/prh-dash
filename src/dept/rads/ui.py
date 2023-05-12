import streamlit as st
from .data import RadsData
from ... import util

def show(data: RadsData):
    """
    Render main content for department
    """
    s = data.stats

    util.st_prh_logo()
    st.title("Radiology")
    st.write(s)