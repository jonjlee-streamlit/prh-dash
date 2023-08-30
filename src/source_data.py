"""
Source data as in-memory copy of all DB tables as dataframes
"""
import logging
import pandas as pd
import streamlit as st
from dataclasses import dataclass, field
from datetime import datetime
from sqlalchemy import create_engine, text as sql_text
from sqlalchemy.orm import Session
from .model import (
    Metadata,
    SourceMetadata,
    Volume,
    BudgetedHoursPerVolume,
    HoursAndFTE,
    IncomeStmt,
)


@dataclass(eq=True, frozen=True)
class SourceData:
    """In-memory copy of DB tables"""

    volume_df: pd.DataFrame = None
    budgeted_hours_per_volume_df: pd.DataFrame = None
    hours_and_fte_df: pd.DataFrame = None
    income_stmt_df: pd.DataFrame = None

    # Metadata
    last_updated: datetime = None
    sources_updated: dict = field(default_factory=dict)


@st.cache_data(show_spinner=False)
def load_db(db_file: str) -> SourceData:
    """
    Read all data from specified SQLite DB into memory and return as dataframes
    """
    logging.info("Reading DB tables")
    engine = create_engine(f"sqlite:///{db_file}")
    with Session(engine) as session:
        # Read metadata
        metadata = (
            session.query(Metadata).order_by(Metadata.last_updated.desc()).first()
        )
        last_updated = metadata.last_updated if metadata is not None else None
        sources_updated = {
            row.filename: row.modified for row in session.query(SourceMetadata)
        }

        # Read dashboard data into dataframes
    dfs = {
        "volume_df": pd.read_sql_table(Volume.__tablename__, engine),
        "budgeted_hours_per_volume_df": pd.read_sql_table(
            BudgetedHoursPerVolume.__tablename__, engine
        ),
        "hours_and_fte_df": pd.read_sql_table(HoursAndFTE.__tablename__, engine),
        "income_stmt_df": pd.read_sql_table(IncomeStmt.__tablename__, engine),
    }

    return SourceData(last_updated=last_updated, sources_updated=sources_updated, **dfs)
