import os
import re
import contextlib
import logging
import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from src.model import (
    Base,
    SourceMetadata,
    Volume,
    BudgetedHoursPerVolume,
    HoursAndFTE,
    IncomeStmt,
)
from src.static_data import WDID_TO_DEPT_NAME, ALIASES_TO_WDID
from src import util

# Logging definitions
logging.basicConfig(level=logging.INFO)
SHOW_SQL_IN_LOG = False

# DB definitions
TMP_DB_FILE = "db-tmp.sqlite3"
DB_FILE = "db.sqlite3"

# Location of data files: <app root>/data/
BASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

# Historical volume data is in the STATS worksheet of the Dashboard Supporting Data spreadsheet
VOLUMES_FILE = os.path.join(BASE_PATH, "Dashboard Supporting Data.xlsx")
VOLUMES_SHEET = "STATS"

BUDGETED_HOURS_FILE = os.path.join(
    BASE_PATH, "Productive Hours per Encounter 2023.xlsx"
)
BUDGETED_HOURS_SHEET = "Summary"

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


def create_schema(engine):
    """
    Create empty tables using defined SQLAlchemy model
    """
    Base.metadata.create_all(engine)


def update_sources_meta(engine, files):
    """
    Populate the sources_meta table with metadata for the source files
    """
    # Get last modified times for each file
    modified = {file: datetime.fromtimestamp(os.path.getmtime(file)) for file in files}

    # Create a session to interact with the database
    with Session(engine) as session:
        for file, modified_time in modified.items():
            source_metadata = SourceMetadata(filename=file, modified=modified_time)
            session.add(source_metadata)
        session.commit()


def sanity_check_data_dir():
    """
    Sanity checks for data directory
    """
    error = None
    if not os.path.isdir(BASE_PATH):
        error = f"ERROR: data directory path does not exist: {BASE_PATH}"
    if not os.path.isfile(VOLUMES_FILE):
        error = f"ERROR: volumes data file is missing: {VOLUMES_FILE}"
    if not os.path.isfile(BUDGETED_HOURS_FILE):
        error = (
            f"ERROR: productive hours summary file is missing: {BUDGETED_HOURS_FILE}"
        )
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


def read_file(filename):
    """
    Wrapper for reading a source data file, returning data as byte array.
    """
    logging.info(filename + " - fetching")
    with open(filename, "rb") as f:
        return f.read()


def read_volume_data(filename, sheet):
    """
    Read the Excel sheet with volume data into a dataframe
    """
    # Read tables from excel worksheet
    logging.info(f"Reading {filename}")
    xl_data = pd.read_excel(filename, sheet_name=sheet, header=None)
    volumes_by_year = util.df_get_tables_by_columns(xl_data, "1:68")

    # Convert from multiple tables:
    #            2022
    #                                    Jan  Feb ....
    # CC_60100   INTENSIVE CARE UNIT      62   44
    #
    # to format we can store to DB:
    #
    # Month     DeptID    DeptName              Volume
    # 2022-01   CC_60100  INTENSIVE CARE UNIT   62
    # ...

    data = []
    for df in volumes_by_year:
        year = util.df_get_val_or_range(df, "C1")

        # Skip header rows x 2 with year and month names
        df = df.iloc[2:]

        # Pull volume data from each row
        for _index, row in df.iterrows():
            # Dept ID and name in the A:B
            dept_wd_id = row.iloc[0]
            dept_name = row.iloc[1]

            # Iterate over volume numbers in columns C:N. enumerate(..., start=1) results in month = [1..12]
            volumes = row.iloc[2 : 2 + 12]
            for month_num, volume in enumerate(volumes, start=1):
                if pd.notnull(volume):
                    # Format month column like "2022-01"
                    month = f"{year:04d}-{month_num:02d}"
                    data.append([dept_wd_id, dept_name, month, volume])

    return pd.DataFrame(data, columns=["dept_wd_id", "dept_name", "month", "volume"])


def read_budgeted_hours_data(filename, sheet):
    """
    Read the Excel sheet with volume data into a dataframe
    """
    # Extract table from Productive Hours per Encounter -> Summary worksheet. Pull Department and Suggested columns
    logging.info(f"Reading {filename}")
    xl_data = pd.read_excel(filename, sheet_name=sheet, header=None)
    hrs_per_encounter_df = util.df_get_table(xl_data, "B2", has_header_row=True)

    # Transform
    # ---------
    # Rename columns to match DB
    hrs_per_encounter_df.rename(
        columns={"Department": "dept_name", "Suggested": "budgeted_hours_per_volume"},
        inplace=True,
    )
    # Add a new column "dept_wd_id" using dict, and drop rows without a known workday dept ID
    hrs_per_encounter_df["dept_wd_id"] = (
        hrs_per_encounter_df["dept_name"]
        .str.lower()
        .map({k.lower(): v for k, v in ALIASES_TO_WDID.items()})
    )
    hrs_per_encounter_df.dropna(subset=["dept_wd_id"], inplace=True)
    # Reassign canonical dept names from workday ID using dict
    hrs_per_encounter_df["dept_name"] = hrs_per_encounter_df["dept_wd_id"].map(
        WDID_TO_DEPT_NAME
    )

    return hrs_per_encounter_df[
        ["dept_wd_id", "dept_name", "budgeted_hours_per_volume"]
    ]


def read_income_stmt_data(files):
    """
    Read and combine data from Excel workbooks for income statements, which are per month
    """
    ret = []
    for file in files:
        # Extract data from first and only worksheet
        # Keep the first 4 columns, Ledger Account, Cost Center, Spend Category, and Revenue Category
        # Keep the actual and budget columns for the month (E:F) and year (L:M)
        logging.info(f"Reading {file}")
        xl_data = pd.read_excel(file, header=None, usecols="A:D,E:F,L:M")

        # There are a couple formats of these files - 2023 files have metadata in the first few rows,
        # but older ones don't. First, find cell with the value of "Ledger Account", which is always
        # in the upper left of the table.
        (row_start, _col) = util.df_find_by_column(xl_data, "Ledger Account")

        # Get the month from the row above the table, column E, which should read "Month to Date: <MM/YYYY>"
        # Convert it to the format YYYY-MM
        # Also, row_idx is 0-based, so to get the row above, just pass in row_idx
        month = util.df_get_val_or_range(xl_data, f"E{row_start}")
        month = datetime.strptime(month, "Month to Date: %m/%Y")
        month = month.strftime("%Y-%m")

        # Drop the non-data rows and apply header row to column names
        income_stmt_df = xl_data.iloc[row_start:]
        income_stmt_df = util.df_convert_first_row_to_column_names(income_stmt_df)

        # Add the month as a column
        income_stmt_df["month"] = month

        # Replace all cells with "(Blank)" with actual nulls
        income_stmt_df = income_stmt_df.replace("(Blank)", None)

        # Rename and reorder columns
        income_stmt_df.columns = [
            "ledger_acct",
            "cost_center",
            "spend_category",
            "revenue_category",
            "actual",
            "budget",
            "actual_ytd",
            "budget_ytd",
            "month",
        ]
        ret.append(income_stmt_df)

    return pd.concat(ret)


def read_historical_hours_and_fte_data(filename):
    """
    Read historical hours/FTE data from the custom formatted Excel workbook
    """
    # Extract data from first and only worksheet
    logging.info(f"Reading {filename}")
    xl_data = pd.read_excel(filename, header=None, usecols="A,B,G,M,N,AB")

    # Loop over tables in worksheet, each one representing a pay period
    ret = []
    last_table_end = 0
    while True:
        # Locate the next table by finding the cell containing "PAY PERIOD" in column A
        table_start = util.df_find_by_column(
            xl_data, "PAY PERIOD", start_cell=f"A{last_table_end+1}"
        )
        if table_start is None:
            break

        # Locate end of the table by finding the cell containing "TOTAL" in column B
        row_start = table_start[0]
        (row_end, _col) = util.df_find_by_column(
            xl_data, "TOTAL", start_cell=f"B{row_start+1}"
        )
        last_table_end = row_end + 1

        # Extract table without 4 header rows or last 3 total rows
        hours_df = xl_data.iloc[row_start + 4 : row_end - 2].copy()
        hours_df.columns = [
            "Department Number",
            "Department Name",
            "prod_hrs",
            "nonprod_hrs",
            "total_hrs",
            "total_fte",
        ]

        # Add the year and pay period number as a column
        hours_df["year"] = HISTORICAL_HOURS_YEAR
        hours_df["pay_period"] = xl_data.iloc[row_start + 1, 0]

        # Transform
        # ---------
        # Add a new column "dept_wd_id" using dict, and drop rows without a known workday dept ID
        hours_df["dept_wd_id"] = (
            hours_df["Department Name"]
            .str.lower()
            .map({k.lower(): v for k, v in ALIASES_TO_WDID.items()})
        )
        hours_df.dropna(subset=["dept_wd_id"], inplace=True)
        # Reassign canonical dept names from workday ID using dict
        hours_df["dept_name"] = hours_df["dept_wd_id"].map(WDID_TO_DEPT_NAME)

        # Reorder and retain columns corresponding to DB table
        ret.append(
            hours_df[
                [
                    "year",
                    "pay_period",
                    "dept_wd_id",
                    "dept_name",
                    "prod_hrs",
                    "nonprod_hrs",
                    "total_hrs",
                    "total_fte",
                ]
            ]
        )

    return pd.concat(ret)


def read_hours_and_fte_data(files):
    """
    Read and combine data from per-month Excel workbooks for productive vs non-productive hours and total FTE
    """
    # There is a PP#n YYYY Payroll_Productivity_by_Cost_Center.xlsx file for each pay period
    ret = []
    for file in files:
        # Extract data from first and only worksheet
        logging.info(f"Reading {file}")
        xl_data = pd.read_excel(file, header=None)

        # Drop any metadata rows prior to start of table, which has the "Department Number" header in the top left.
        (row_start, _col) = util.df_find_by_column(xl_data, "Department Number")
        hours_df = xl_data.iloc[row_start:]
        hours_df = util.df_convert_first_row_to_column_names(hours_df)

        # Drop next row, which are sub-headers. Keep specific columns as listed below.
        # Find columns by name, because there are a couple different formats with different columns orders.
        hours_df = hours_df.loc[
            1:,
            [
                "Department Number",
                "Department Name",
                "Total Productive Hours",
                "Total Non-Productive Hours",
                "Total Productive/Non-Productive Hours",
                "Total FTE",
            ],
        ]

        # Read year and pay period number from file name
        year_pp_num = re.search(r"PP#(\d+) (\d+) ", file, re.IGNORECASE)
        hours_df["year"] = year_pp_num.group(2)
        hours_df["pay_period"] = year_pp_num.group(1)

        # Transform
        # ---------
        # Add a new column "dept_wd_id" using dict, and drop rows without a known workday dept ID
        hours_df["dept_wd_id"] = (
            hours_df["Department Name"]
            .str.lower()
            .map({k.lower(): v for k, v in ALIASES_TO_WDID.items()})
        )
        hours_df.dropna(subset=["dept_wd_id"], inplace=True)
        # Reassign canonical dept names from workday ID using dict
        hours_df["dept_name"] = hours_df["dept_wd_id"].map(WDID_TO_DEPT_NAME)

        # Rename and reorder columns
        hours_df.rename(
            columns={
                "Total Productive Hours": "prod_hrs",
                "Total Non-Productive Hours": "nonprod_hrs",
                "Total Productive/Non-Productive Hours": "total_hrs",
                "Total FTE": "total_fte",
            },
            inplace=True,
        )
        ret.append(
            hours_df[
                [
                    "year",
                    "pay_period",
                    "dept_wd_id",
                    "dept_name",
                    "prod_hrs",
                    "nonprod_hrs",
                    "total_hrs",
                    "total_fte",
                ]
            ]
        )

    return pd.concat(ret)


def clear_table_and_insert_data(session, table, df, df_column_order=None):
    """
    Deletes rows from the given table and reinsert data from dataframe
    table is a SQLAlchemy mapped class
    df_column_order specifies the names of the columns in df so they match the order of the table's SQLAlchemy definition
    """
    # Clear data in DB table
    session.query(table).delete()
    session.commit()

    # Reorder columns to match SQLAlchema table definition
    if df_column_order is not None:
        df = df[df_column_order]

    # Load data into table using Pandas to_sql
    logging.info(f"Loading table {table}")
    df.to_sql(
        table.__tablename__,
        con=session.bind,
        index=False,
        if_exists="append",
        method="multi",
    )


if __name__ == "__main__":
    # Sanity check data directory expected location and files
    if not sanity_check_data_dir():
        logging.error("ERROR: data directory error (see above). Terminating.")
        exit(1)

    # Get list of dynamic data files, ie data organized as one Excel workbook per month
    income_stmt_files = find_data_files(INCOME_STMT_PATH)
    hours_files = find_data_files(HOURS_PATH, exclude=[HISTORICAL_HOURS_FILE])
    source_files = (
        [VOLUMES_FILE, BUDGETED_HOURS_FILE, HISTORICAL_HOURS_FILE]
        + income_stmt_files
        + hours_files
    )
    logging.info(f"Discovered source files: {source_files}")

    # TODO: data verification
    # - VOLUMES_FILE, List worksheet: verify same data as static_data.WDID_TO_DEPTNAME
    # - BUDGETED_HOURS_FILE, Summary worksheet: verify Department and Suggested columns present
    # - Each income statement sheet has Ledger Account cell, and data in columns A:Q

    # Create the empty temporary database file
    with contextlib.suppress(FileNotFoundError):
        os.remove(TMP_DB_FILE)
    db = create_engine(f"sqlite:///{TMP_DB_FILE}", echo=SHOW_SQL_IN_LOG)
    create_schema(db)
    logging.info(f"Created tables in {TMP_DB_FILE}")

    # Extract and perform basic transformation of data from spreadsheets
    volumes_df = read_volume_data(VOLUMES_FILE, VOLUMES_SHEET)
    budgeted_hours_df = read_budgeted_hours_data(
        BUDGETED_HOURS_FILE, BUDGETED_HOURS_SHEET
    )
    income_stmt_df = read_income_stmt_data(income_stmt_files)
    historical_hours_df = read_historical_hours_and_fte_data(HISTORICAL_HOURS_FILE)
    hours_df = read_hours_and_fte_data(hours_files)
    hours_df = pd.concat([historical_hours_df, hours_df])

    # Load data into DB. Clear each table prior to loading from dataframe
    with Session(db) as session:
        clear_table_and_insert_data(session, Volume, volumes_df)
        clear_table_and_insert_data(session, BudgetedHoursPerVolume, budgeted_hours_df)
        clear_table_and_insert_data(session, HoursAndFTE, hours_df)
        clear_table_and_insert_data(session, IncomeStmt, income_stmt_df)

    # Update modified times for source data files
    update_sources_meta(db, source_files)

    # Move new database in place
    db.dispose()
    os.replace(TMP_DB_FILE, DB_FILE)
