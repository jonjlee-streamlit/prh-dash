"""
Defines data classes that hold raw and processed source data
"""
import pandas as pd
from dataclasses import dataclass


@dataclass(eq=True, frozen=True)
class RawData:
    """Represents raw data read from Excel spreadsheets generated from various sources including Epic and Workday"""

    # All imported data
    raw: pd.DataFrame


@dataclass
class ProcessedData:
    """Represents processed data including"""

    # Original data set
    raw: pd.DataFrame

    # Processed data set
    all: pd.DataFrame


def parse(filename: str, contents: bytes) -> RawData:
    """
    Detects the file type using a filename and its contents and converts it to a DataFrame containing the raw data.
    """
    pass
