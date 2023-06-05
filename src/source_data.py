"""
Defines data classes that hold raw and processed source data
"""
import io
import logging
import pandas as pd
import openpyxl as xl
import streamlit as st
from .RawData import RawData
from . import dept

_PARSERS = [dept.therapy.parser, dept.rads.parser]


@st.cache_data(show_spinner=False)
def extract_from(files: list[str]) -> RawData:
    """
    Read and parse a list of source data files, including for example, Excel reports exported from Workday
    """
    # Read all files
    segments = []
    for filename in files:
        # Fetch and read file into memory
        contents = _read_file(filename)
        segment = _parse(filename, contents)
        if segment is not None:
            segments.append(segment)

    if len(segments) == 0:
        return None

    # Merge multiple files into one object if necessary
    raw_data = RawData.merge(segments) if len(segments) > 1 else segments[0]
    return raw_data


def _read_file(filename: str) -> bytes:
    """
    Wrapper for reading a source data file, returning data as byte array.
    In the future, will allow for fetching from URL and handling encrypted data.
    """
    logging.info(filename + " - fetching")
    with open(filename, "rb") as f:
        return f.read()


def _parse(filename: str, contents: bytes) -> RawData:
    """
    Delegate to department specific parsers to detect file type and pull contents into memory
    """
    # Get list of worksheets if files is an excel spreadsheet
    wb = None
    excel_sheets = []
    if filename.endswith(".xlsx"):
        try:
            wb = xl.load_workbook(io.BytesIO(contents), read_only=True, data_only=True)
            excel_sheets = wb.sheetnames
        except Exception as e:
            logging.info(f"Could not read Excel file {filename}: {e}")
        finally:
            if wb is not None:
                wb.close()

    # Try each available parser until file type recognized
    for p in _PARSERS:
        raw_data = p.parse(filename, contents, excel_sheets)
        if raw_data is not None:
            return raw_data

    logging.info(f"{filename} - skipping; no parser available.")
    return None
