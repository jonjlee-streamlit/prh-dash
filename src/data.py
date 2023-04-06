import logging
import pandas as pd
from .source_data import RawData, ProcessedData, parse


def extract_from(files: list[str]) -> RawData:
    """
    Read and parse a list of source data files, including for example, Excel reports exported from Workday
    """
    # Read all files and merge data into one object
    segments = []
    for filename in files:
        # Fetch and read file into memory
        contents = _read_file(filename)
        segment = parse(filename, contents)
        segments.append(segment)

    raw_data = _merge(segments)
    return raw_data


def process(raw: RawData) -> ProcessedData:
    """
    Receives raw source data from extract_from(). Partitions and computes statistics to be displayed by the app.
    """
    return ProcessedData(raw=raw, all=None)


def _read_file(filename: str) -> bytes:
    """
    Wrapper for reading a source data file, returning data as byte array.
    In the future, will allow for fetching from URL and handling encrypted data.
    """
    logging.info("Fetching " + filename)
    with open(filename, "rb") as f:
        return f.read()


def _merge(segments: list[RawData]) -> RawData:
    """Merges data from several RawData objects which hold data from the source data files"""
    # Concatenate all DataFrames from segments
    revenue = pd.concat([segment.revenue for segment in segments], ignore_index=True)
    deductions = pd.concat(
        [segment.deductions for segment in segments], ignore_index=True
    )
    expenses = pd.concat([segment.expenses for segment in segments], ignore_index=True)
    volume = pd.concat([segment.volume for segment in segments], ignore_index=True)
    hours = pd.concat([segment.hours for segment in segments], ignore_index=True)

    # Create a new RawData instance with the concatenated DataFrame
    merged_data = RawData(
        revenue=revenue,
        deductions=deductions,
        expenses=expenses,
        volume=volume,
        hours=hours,
    )
    return merged_data
