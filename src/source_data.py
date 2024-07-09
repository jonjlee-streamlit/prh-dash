"""
Source data as in-memory copy of all DB tables as dataframes
"""

import logging
import os
import pandas as pd
import streamlit as st
import requests
from dataclasses import dataclass, field
from datetime import datetime
from sqlalchemy import create_engine, text as sql_text
from sqlalchemy.orm import Session
from . import encrypt
from .model import (
    Metadata,
    SourceMetadata,
    Volume,
    UOS,
    Budget,
    Hours,
    ContractedHours,
    IncomeStmt,
)

# Path to default app database
DEFAULT_DB_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "db.sqlite3"
)


@dataclass(eq=True, frozen=True)
class SourceData:
    """In-memory copy of DB tables"""

    volumes_df: pd.DataFrame = None
    uos_df: pd.DataFrame = None
    budget_df: pd.DataFrame = None
    hours_df: pd.DataFrame = None
    contracted_hours_df: pd.DataFrame = None
    income_stmt_df: pd.DataFrame = None

    # Metadata
    last_updated: datetime = None
    sources_updated: dict = field(default_factory=dict)
    contracted_hours_updated_month: str = None


@st.cache_data(show_spinner=False)
def from_db(db_file: str) -> SourceData:
    """
    Read all data from specified SQLite DB into memory and return as dataframes
    """
    logging.info("Reading DB tables")
    if not os.path.exists(db_file):
        return None

    engine = create_engine(f"sqlite:///{db_file}")
    with Session(engine) as session:
        # Read metadata
        metadata = {
            "last_updated": session.query(Metadata.last_updated)
            .order_by(Metadata.last_updated.desc())
            .scalar(),
            "contracted_hours_updated_month": session.query(
                Metadata.contracted_hours_updated_month
            ).scalar(),
            "sources_updated": {
                row.filename: row.modified for row in session.query(SourceMetadata)
            },
        }

    # Read dashboard data into dataframes
    dfs = {
        "volumes_df": pd.read_sql_table(Volume.__tablename__, engine),
        "uos_df": pd.read_sql_table(UOS.__tablename__, engine),
        "budget_df": pd.read_sql_table(Budget.__tablename__, engine),
        "hours_df": pd.read_sql_table(Hours.__tablename__, engine),
        "contracted_hours_df": pd.read_sql_table(ContractedHours.__tablename__, engine),
        "income_stmt_df": pd.read_sql_table(IncomeStmt.__tablename__, engine),
    }

    engine.dispose()
    return SourceData(**metadata, **dfs)


def fetch_source_file_to_disk(file, url, key, force=False):
    """
    Fetch source data from URL, decrypt, and store to disk if not already present.
    If force is True, always fetch.
    """
    if not os.path.exists(file) or force:
        if not (url and key):
            logging.info(f"Unable to fetch remote data file. URL and key required.")
            return

        # Fetch source data from URL
        logging.info(f"Fetching data from {url}")
        res = requests.get(url)
        if res.status_code == 200:
            # Decrypt and write to disk
            data = encrypt.decrypt(res.content, key)
            with open(file, "wb") as f:
                f.write(data)

            # Force data module to reread data from disk on next run
            st.cache_data.clear()
        else:
            st.write(f"Unable to fetch data file, status code {res.status_code}.")
