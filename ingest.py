import os
import logging
import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from src.model import Base, SourceMetadata
from src import util

# DB definitions
DB_FILE = "db.sqlite3"

# Location of data files: <app root>/data/
BASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

# Historical volume data is in the STATS worksheet of the Dashboard Supporting Data spreadsheet
VOLUMES_FILE = os.path.join(BASE_PATH, "Dashboard Supporting Data.xlsx")
VOLUMES_SHEET = "STATS"

BUDGETED_HOURS_FILE = os.path.join(
    BASE_PATH, "Productive Hours per Encounter 2023.xlsx"
)

# The Natural Class subdir contains income statment in one Excel file per month, eg,
# ./Natural Class/2022/(01) Jan 2022 Natural Class.xlsx",
INCOME_STMT_PATH = os.path.join(BASE_PATH, "Natural Class")

# The PayPeriod subdir contains two types of excel files with hours/FTE information.
# History data is in PayPeriod/2022/PP#1-PP#25 Payroll Productivity.xlsx
# The other files contain data for a single pay period, eg,
# PayPeriod/2022/PP#26 2022 Payroll_Productivity_by_Cost_Center.xlsx
HISTORICAL_FTE_PATH = FTE_PATH = os.path.join(
    BASE_PATH, "PayPeriod", "2022", "PP#1-PP#25 Payroll Productivity.xlsx"
)
FTE_PATH = os.path.join(BASE_PATH, "PayPeriod")


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


def verify_data_dir():
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
    if not os.path.isdir(FTE_PATH) or len(find_data_files(FTE_PATH)) == 0:
        error = f"ERROR: productivity data root directory is empty: {FTE_PATH}"

    if error is not None:
        print(error)
        return False
    return True


def find_data_files(path):
    """
    Return list of full path for all files in a directory recursively.
    Filter out any files starting with . or ~.
    """
    ret = []
    for dirpath, _dirnames, files in os.walk(path):
        for file in files:
            # Filter out temporary files: anything that starts with . or ~
            if not file.startswith(".") and not file.startswith("~"):
                ret.append(os.path.join(dirpath, file))
    return ret


def read_file(filename):
    """
    Wrapper for reading a source data file, returning data as byte array.
    """
    logging.info(filename + " - fetching")
    with open(filename, "rb") as f:
        return f.read()


def read_volume_data(filename):
    """
    Read the Excel sheet with volume data into a dataframe
    """
    # Read tables from excel worksheet
    xl_data = pd.read_excel(filename, sheet_name=VOLUMES_SHEET, header=None)
    volumes_by_year = util.df_get_tables_by_columns(xl_data, "1:68")

    # Convert from multiple tables:
    #            2022
    #                                    Jan  Feb ....
    # CC_60100   INTENSIVE CARE UNIT      62   44
    #
    # to format we can store to DB:
    #
    # Year   Month   DeptID    DeptName              Volume
    # 2022   01      CC_60100  INTENSIVE CARE UNIT   62
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
            for month, volume in enumerate(volumes, start=1):
                if pd.notnull(volume):
                    data.append([dept_wd_id, dept_name, year, month, volume])

    return pd.DataFrame(
        data, columns=["dept_wd_id", "dept_name", "year", "month", "volume"]
    )


if __name__ == "__main__":
    # Sanity check data directory expected location and files
    if not verify_data_dir():
        print("ERROR: data directory error (see above). Terminating.")
        exit(1)

    # Create the empty SQLite database file
    engine = create_engine(f"sqlite:///{DB_FILE}", echo=True)
    create_schema(engine)

    # Read volume data
    df = read_volume_data(VOLUMES_FILE)
    print(df)

    # Update modified times for source data files
    income_stmt_files = find_data_files(INCOME_STMT_PATH)
    fte_files = find_data_files(FTE_PATH)
    source_files = [VOLUMES_FILE, BUDGETED_HOURS_FILE] + income_stmt_files + fte_files
    update_sources_meta(engine, source_files)
