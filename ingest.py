import os
import contextlib
import logging
import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from src.model import (
    Volume,
    Budget,
    Hours,
    HoursByPayPeriod,
    IncomeStmt,
)
from src.source_data import DEFAULT_DB_FILE
from src.ingest import db, parse, transform

# Logging definitions
logging.basicConfig(level=logging.INFO)
SHOW_SQL_IN_LOG = False

# Temporary DB to ingest data into
TMP_DB_FILE = "db-tmp.sqlite3"

# Location of data files: <app root>/data/
BASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

# Historical volume data is in the STATS worksheet of the Dashboard Supporting Data spreadsheet
VOLUMES_FILE = os.path.join(BASE_PATH, "Dashboard Supporting Data.xlsx")
VOLUMES_SHEET = "STATS"
VOLUMES_BUDGET_SHEET = "Data"

# The Natural Class subdir contains income statment in one Excel file per month, eg,
# ./Natural Class/2022/(01) Jan 2022 Natural Class.xlsx
INCOME_STMT_PATH = os.path.join(BASE_PATH, "Natural Class")

# PayPeriod subdir contians productive / non-productive hours and FTE data per month. eg,
#   ./PayPeriod/2023/PP#1 2023 Payroll_Productivity_by_Cost_Center.xlsx
# In addition, historical data for 2022 PP#1-25, which includes the clinic network, is lumped together a separate file:
#   ./PayPeriod/2023/PP#1-PP#25 Payroll Productivity.xlsx
HISTORICAL_HOURS_YEAR = 2022
HISTORICAL_HOURS_FILE = os.path.join(
    BASE_PATH, "PayPeriod", "2022", "PP#1-PP#25 Payroll Productivity.xlsx"
)
HOURS_PATH = os.path.join(BASE_PATH, "PayPeriod")


def sanity_check_data_dir():
    """
    Sanity checks for data directory
    """
    error = None
    if not os.path.isdir(BASE_PATH):
        error = f"ERROR: data directory path does not exist: {BASE_PATH}"
    if not os.path.isfile(VOLUMES_FILE):
        error = f"ERROR: volumes data file is missing: {VOLUMES_FILE}"
    if (
        not os.path.isdir(INCOME_STMT_PATH)
        or len(find_data_files(INCOME_STMT_PATH)) == 0
    ):
        error = f"ERROR: income statements root directory is empty: {INCOME_STMT_PATH}"
    if not os.path.isdir(HOURS_PATH) or len(find_data_files(HOURS_PATH)) == 0:
        error = f"ERROR: productivity data root directory is empty: {HOURS_PATH}"

    if error is not None:
        print(error)
        return False
    return True


def find_data_files(path, exclude=None):
    """
    Return list of full path for all files in a directory recursively.
    Filter out any files starting with . or ~.
    """
    ret = []
    for dirpath, _dirnames, files in os.walk(path):
        for file in files:
            # Filter out temporary files: anything that starts with . or ~
            if not file.startswith(".") and not file.startswith("~"):
                # Filter out explicitly excluded files
                filepath = os.path.join(dirpath, file)
                if exclude is None or filepath not in exclude:
                    ret.append(filepath)

    return sorted(ret)


if __name__ == "__main__":
    # Sanity check data directory expected location and files
    if not sanity_check_data_dir():
        logging.error("ERROR: data directory error (see above). Terminating.")
        exit(1)

    # Get list of dynamic data files, ie data organized as one Excel workbook per month
    income_stmt_files = find_data_files(INCOME_STMT_PATH)
    hours_files = find_data_files(HOURS_PATH, exclude=[HISTORICAL_HOURS_FILE])
    source_files = (
        [VOLUMES_FILE, HISTORICAL_HOURS_FILE] + income_stmt_files + hours_files
    )
    source_files_str = "\n  ".join(source_files)
    logging.info(f"Discovered source files:\n  {source_files_str}")

    # TODO: data verification
    # - VOLUMES_FILE, List worksheet: verify same data as static_data.WDID_TO_DEPTNAME
    # - Each income statement sheet has Ledger Account cell, and data in columns A:Q
    # - hours and income data is present for the latest month we have volume data for

    # Create the empty temporary database file
    with contextlib.suppress(FileNotFoundError):
        os.remove(TMP_DB_FILE)
    db_engine = create_engine(f"sqlite:///{TMP_DB_FILE}", echo=SHOW_SQL_IN_LOG)
    db.create_schema(db_engine)
    logging.info(f"Created tables in {TMP_DB_FILE}")

    # Extract and perform basic transformation of data from spreadsheets
    volumes_df = parse.read_volume_data(VOLUMES_FILE, VOLUMES_SHEET)
    budget_df = parse.read_budget_data(VOLUMES_FILE, VOLUMES_BUDGET_SHEET)
    income_stmt_df = parse.read_income_stmt_data(income_stmt_files)
    historical_hours_df = parse.read_historical_hours_and_fte_data(
        HISTORICAL_HOURS_FILE, HISTORICAL_HOURS_YEAR
    )
    hours_by_pay_period_df = parse.read_hours_and_fte_data(hours_files)
    hours_by_pay_period_df = pd.concat([historical_hours_df, hours_by_pay_period_df])

    # Transform hours data to months
    hours_by_month_df = transform.transform_hours_from_pay_periods_to_months(
        hours_by_pay_period_df
    )

    # Load data into DB. Clear each table prior to loading from dataframe
    with Session(db_engine) as session:
        db.clear_table_and_insert_data(session, Volume, volumes_df)
        db.clear_table_and_insert_data(session, Budget, budget_df)
        db.clear_table_and_insert_data(
            session, HoursByPayPeriod, hours_by_pay_period_df
        )
        db.clear_table_and_insert_data(session, Hours, hours_by_month_df)
        db.clear_table_and_insert_data(session, IncomeStmt, income_stmt_df)

    # Update last ingest time and modified times for source data files
    modified = {
        file: datetime.fromtimestamp(os.path.getmtime(file)) for file in source_files
    }
    db.update_meta(db_engine, modified)

    # Move new database in place
    db_engine.dispose()
    os.replace(TMP_DB_FILE, DEFAULT_DB_FILE)
