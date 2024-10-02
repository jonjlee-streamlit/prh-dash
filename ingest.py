import os
import contextlib
import logging
import argparse
import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from src.model import (
    Volume,
    UOS,
    Budget,
    Hours,
    ContractedHours,
    HoursByPayPeriod,
    IncomeStmt,
)
from src.source_data import DEFAULT_DB_FILE
from src.ingest import db, parse, transform, sanity

# Opt into pandas 3 behavior for replace() and fillna(), where columns of object dtype are NOT changed to something more specific,
# like int/float/str. This option can be removed once upgrading pandas 2-> 3.
pd.set_option("future.no_silent_downcasting", True)

# Logging definitions
logging.basicConfig(level=logging.INFO)
SHOW_SQL_IN_LOG = False

# Temporary DB to ingest data into
TMP_DB_FILE = "db-tmp.sqlite3"

# Specific worksheet names containing data to ingest in the Dashboard Supporting Data spreadsheet
VOLUMES_SHEET = "STATS"
UOS_SHEET = "UOS"
VOLUMES_BUDGET_SHEET = "Data"
HRS_PER_VOLUME_SHEET = "Prod.MH UOS"
CONTRACTED_HRS_SHEET = "ProdHrs"

# The historical hours data returned by get_file_paths() as historical_hours_file contains data for 2022
HISTORICAL_HOURS_YEAR = 2022

def parse_arguments():
    parser = argparse.ArgumentParser(description="Ingest data into the database.")
    parser.add_argument("data_dir", help="Path to the data directory")
    parser.add_argument("-o", "--out", help="Output database file path")
    return parser.parse_args()

def get_file_paths(base_path):
    # Historical volume data is ion the Dashboard Supporting Data spreadsheet
    volumes_file = os.path.join(base_path, "Dashboard Supporting Data 2024 v3.xlsx")

    # The Natural Class subdir contains income statment in one Excel file per month, eg,
    # ./Natural Class/2022/(01) Jan 2022 Natural Class.xlsx
    income_stmt_path = os.path.join(base_path, "Natural Class")

    # PayPeriod subdir contians productive / non-productive hours and FTE data per month. eg,
    #   ./PayPeriod/2023/PP#1 2023 Payroll_Productivity_by_Cost_Center.xlsx
    # In addition, historical data for 2022 PP#1-25, which includes the clinic network, is lumped together a separate file:
    #   ./PayPeriod/2023/PP#1-PP#25 Payroll Productivity.xlsx
    historical_hours_file = os.path.join(base_path, "PayPeriod", "2022", "PP#1-PP#26 Payroll Productivity.xlsx")
    hours_path = os.path.join(base_path, "PayPeriod")

    return volumes_file, income_stmt_path, hours_path, historical_hours_file

def sanity_check_data_dir(base_path, volumes_file, income_stmt_path, hours_path):
    """
    Sanity checks for data directory
    """
    error = None
    if not os.path.isdir(base_path):
        error = f"ERROR: data directory path does not exist: {base_path}"
    if not os.path.isfile(volumes_file):
        error = f"ERROR: volumes data file is missing: {volumes_file}"
    if (
        not os.path.isdir(income_stmt_path)
        or len(find_data_files(income_stmt_path)) == 0
    ):
        error = f"ERROR: income statements root directory is empty: {income_stmt_path}"
    if not os.path.isdir(hours_path) or len(find_data_files(hours_path)) == 0:
        error = f"ERROR: productivity data root directory is empty: {hours_path}"

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

def main():
    args = parse_arguments()
    base_path = args.data_dir
    output_db_file = args.out or DEFAULT_DB_FILE

    volumes_file, income_stmt_path, hours_path, historical_hours_file = get_file_paths(base_path)

    # Sanity check data directory expected location and files
    if not sanity_check_data_dir(base_path, volumes_file, income_stmt_path, hours_path):
        logging.error("ERROR: data directory error (see above). Terminating.")
        exit(1)

    # Get list of dynamic data files, ie data organized as one Excel workbook per month
    income_stmt_files = find_data_files(income_stmt_path)
    hours_files = find_data_files(hours_path, exclude=[historical_hours_file])
    source_files = (
        [volumes_file, historical_hours_file] + income_stmt_files + hours_files
    )
    source_files_str = "\n  ".join(source_files)
    logging.info(f"Discovered source files:\n  {source_files_str}")

    # TODO: data verification
    # - volumes_file, List worksheet: verify same data as static_data.WDID_TO_DEPTNAME
    # - Each income statement sheet has Ledger Account cell, and data in columns A:Q
    # - hours and income data is present for the latest month we have volume data for
    # - fte, volumes should all be non-negative. Hours can be negative for adjustments
    if not sanity.check_data_files(volumes_file, income_stmt_files):
        logging.error("ERROR: data files sanity check failed (see above).")
        exit(1)

    # Create the empty temporary database file
    with contextlib.suppress(FileNotFoundError):
        os.remove(TMP_DB_FILE)
    db_engine = create_engine(f"sqlite:///{TMP_DB_FILE}", echo=SHOW_SQL_IN_LOG)
    db.create_schema(db_engine)
    logging.info(f"Created tables in {TMP_DB_FILE}")

    # Extract and perform basic transformation of data from spreadsheets
    volumes_df = parse.read_volume_and_uos_data(volumes_file, VOLUMES_SHEET)
    uos_df = parse.read_volume_and_uos_data(volumes_file, UOS_SHEET)
    budget_df = parse.read_budget_data(
        volumes_file, VOLUMES_BUDGET_SHEET, HRS_PER_VOLUME_SHEET, UOS_SHEET
    )
    contracted_hours_updated_month, contracted_hours_df = (
        parse.read_contracted_hours_data(volumes_file, CONTRACTED_HRS_SHEET)
    )
    income_stmt_df = parse.read_income_stmt_data(income_stmt_files)
    historical_hours_df = parse.read_historical_hours_and_fte_data(
        historical_hours_file, HISTORICAL_HOURS_YEAR
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
        db.clear_table_and_insert_data(session, UOS, uos_df)
        db.clear_table_and_insert_data(session, Budget, budget_df)
        db.clear_table_and_insert_data(
            session, HoursByPayPeriod, hours_by_pay_period_df
        )
        db.clear_table_and_insert_data(session, Hours, hours_by_month_df)
        db.clear_table_and_insert_data(session, ContractedHours, contracted_hours_df)
        db.clear_table_and_insert_data(session, IncomeStmt, income_stmt_df)

    # Update last ingest time and modified times for source data files
    modified = {
        file: datetime.fromtimestamp(os.path.getmtime(file)) for file in source_files
    }
    db.update_meta(db_engine, modified, contracted_hours_updated_month)

    # Move new database in place
    db_engine.dispose()
    os.replace(TMP_DB_FILE, output_db_file)
    logging.info(f"Output to {output_db_file}")


if __name__ == "__main__":
    main();