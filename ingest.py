import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.model import Base

# DB definitions
DB_FILE = "db.sqlite3"

# Location of data files: <app root>/data/
BASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

# Historical volume data is in the STATS worksheet of the Dashboard Supporting Data spreadsheet
VOLUMES_FILE = os.path.join(BASE_PATH, "Dashboard Supporting Data.xlsx")

# The Natural Class subdir contains income statment in one Excel file per month, eg,
# ./Natural Class/2022/(01) Jan 2022 Natural Class.xlsx",
INCOME_STMT_PATH = os.path.join(BASE_PATH, "Natural Class")

# The PayPeriod subdir contains two types of excel files with hours/FTE information.
# History data is in PayPeriod/2022/PP#1-PP#25 Payroll Productivity.xlsx
# The other files contain data for a single pay period, eg,
# PayPeriod/2022/PP#26 2022 Payroll_Productivity_by_Cost_Center.xlsx
FTE_PATH = os.path.join(BASE_PATH, "PayPeriod")


def create_db(filename):
    """
    Create empty database using defined SQLAlchemy model
    """
    # Create the SQLite database file
    engine = create_engine(f"sqlite:///{filename}", echo=True)

    # Create the tables in the database
    Base.metadata.create_all(engine)

    # Create a session to interact with the database
    Session = sessionmaker(bind=engine)
    session = Session()

    # Commit the changes to the database
    session.commit()

    # Close the session
    session.close()


def verify_data_dir():
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


if __name__ == "__main__":
    # Sanity check data directory expected location and files
    if not verify_data_dir():
        print("ERROR: data directory error (see above). Terminating.")
        exit(1)

    income_stmt_files = find_data_files(INCOME_STMT_PATH)
    fte_files = find_data_files(FTE_PATH)

    # Create empty DB file
    create_db(DB_FILE)
