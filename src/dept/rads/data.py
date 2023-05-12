import pandas as pd
from dataclasses import dataclass
from ...source_data import RawData

@dataclass
class RadsData:
    """Represents processed department specific data"""

    # Original data set
    raw: RawData

    # Calculated statistics
    stats: dict


def process(raw: RawData) -> RadsData:
    """
    Receives raw source data from extract_from().
    Partitions and computes statistics to be displayed by the app.
    This dept currently does not have any user parameters from sidebar.
    """
    stats = _calc_stats(raw)
    return RadsData(raw=raw, stats=stats)

def _calc_stats(raw: RawData) -> dict:
    """Precalculate statistics from raw data that will be displayed on dashboard"""
    s = {}
    return s