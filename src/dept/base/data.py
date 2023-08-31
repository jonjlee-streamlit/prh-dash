"""
Transform source data into department specific data that can be displayed on dashboard
"""

import pandas as pd
from dataclasses import dataclass
from .depts import DeptConfig
from ...source_data import SourceData


@dataclass(frozen=True)
class DeptData:
    # Settings
    dept: str
    month: str

    # Patient volumes from stats report card
    volumes: pd.DataFrame

    # Productive / Non-productive hours
    hours: pd.DataFrame

    # Income statement for a specific department and time period
    income_stmt: pd.DataFrame

    # Single value calculations, like YTD volume
    stats: dict


def process(config: DeptConfig, settings: dict, src: SourceData) -> DeptData:
    """
    Receives raw source data from database.
    Partitions and computes statistics to be displayed by the app.
    settings contains any configuration from the sidebar that the user selects.
    """
    dept, month = settings["dept"], settings["month"]
