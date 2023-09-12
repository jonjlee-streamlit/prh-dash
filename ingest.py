import os
import re
import contextlib
import logging
import calendar
import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from src.model import (
    Base,
    Metadata,
    SourceMetadata,
    Volume,
    Budget,
    Hours,
    HoursByPayPeriod,
    IncomeStmt,
)
from src.source_data import DEFAULT_DB_FILE
from src.static_data import WDID_TO_DEPT_NAME, ALIASES_TO_WDID
from src import util

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

# Starting point for converting bi-weekly pay period number to start and end dates. Set to the start date of pay period 1 for the given year.
# Pay periods go from Saturday -> Friday two weeks later, and the pay date is on the Friday following the pay period.
PAY_PERIOD_ANCHOR_DATE = {
    "year": 2023,
    "start_date": datetime(2022, 12, 31),
}


def create_schema(engine):
    """
    Create empty tables using defined SQLAlchemy model
    """
    Base.metadata.create_all(engine)


def update_meta(engine, files):
    """
    Populate the sources_meta table with metadata for the source files
    """
    # Get last modified times for each file
    modified = {file: datetime.fromtimestamp(os.path.getmtime(file)) for file in files}

    # Write timestamps to DB
    logging.info("Writing metadata")
    with Session(engine) as session:
        # Clear metadata tables
        session.query(Metadata).delete()
        session.query(SourceMetadata).delete()
        session.commit()

        # Set last ingest time
        session.add(Metadata(last_updated=datetime.now()))

        # Store last modified timestamps for ingested files
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
    logging.info(f"Reading {filename}, {sheet}")
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


def read_budget_data(filename, sheet):
    """
    Read the sheet from the Dashboard Supporting Data Excel workbook with budgeted hours and volume data into a dataframe
    """
    # Extract table and assign column names that match DB schema for columns we will retain
    logging.info(f"Reading {filename}, {sheet}")
    xl_data = pd.read_excel(filename, sheet_name=sheet, header=None)
    budget_df = util.df_get_tables_by_rows(
        xl_data, cols="B:L", start_row_idx=6, limit=1
    )
    budget_df = budget_df[0]
    budget_df.columns = [
        "dept_wd_id",
        "dept_name",
        "budget_fte",
        "Budgeted Hours",
        "% Productive",
        "budget_prod_hrs",
        "budget_volume",
        "budget_prod_hrs_per_volume",
        "",
        "hourly_rate",
        "Current YTD FTE",
    ]

    # Transform
    # ---------
    # Drop columns without an Workday ID
    budget_df.dropna(subset=["dept_wd_id"], inplace=True)

    return budget_df[
        [
            "dept_wd_id",
            "dept_name",
            "budget_fte",
            "budget_prod_hrs",
            "budget_volume",
            "budget_prod_hrs_per_volume",
            "hourly_rate",
        ]
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

        # Drop the non-data rows and rename columns
        income_stmt_df = xl_data.iloc[row_start:]
        income_stmt_df = income_stmt_df.iloc[1:].reset_index(drop=True)
        income_stmt_df.columns = [
            "ledger_acct",
            "Cost Center",
            "spend_category",
            "revenue_category",
            "actual",
            "budget",
            "actual_ytd",
            "budget_ytd",
        ]

        # Add a new column "dept_wd_id" converting the Cost Center to an ID. Drop rows without a known workday dept ID
        # Reassign canonical dept names from workday ID into the dept_name column
        income_stmt_df["dept_wd_id"] = (
            income_stmt_df["Cost Center"]
            .str.lower()
            .map({k.lower(): v for k, v in ALIASES_TO_WDID.items()})
        )
        unrecognized = (
            income_stmt_df[income_stmt_df["dept_wd_id"].isna()]
            .loc[:, "Cost Center"]
            .unique()
        )
        income_stmt_df.dropna(subset=["dept_wd_id"], inplace=True)
        income_stmt_df["dept_name"] = income_stmt_df["dept_wd_id"].map(
            WDID_TO_DEPT_NAME
        )

        # Log unrecognized cost centers that were dropped from data:
        if len(unrecognized) > 0 and unrecognized[0] != "(Blank)":
            logging.warn(
                f"Dropping unknown cost centers from income statement: {unrecognized} in {file}"
            )

        # Add the month as a column
        income_stmt_df["month"] = month

        # Replace all cells with "(Blank)" with actual empty string
        income_stmt_df = income_stmt_df.replace("(Blank)", "")

        # Reorder and retain columns corresponding to DB table
        ret.append(
            income_stmt_df[
                [
                    "month",
                    "ledger_acct",
                    "dept_wd_id",
                    "dept_name",
                    "spend_category",
                    "revenue_category",
                    "actual",
                    "budget",
                    "actual_ytd",
                    "budget_ytd",
                ]
            ]
        )

    return pd.concat(ret)


def read_historical_hours_and_fte_data(filename):
    """
    Read historical hours/FTE data from the custom formatted Excel workbook
    """
    # Extract data from first and only worksheet
    logging.info(f"Reading {filename}")
    xl_data = pd.read_excel(filename, header=None, usecols="A,B,C,D,E,G,M,N,AB")

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
            "reg_hrs",
            "ot_hrs",
            "premium_hrs",
            "prod_hrs",
            "nonprod_hrs",
            "total_hrs",
            "total_fte",
        ]

        # Add the pay period number in the format YYYY-##
        pp_num = xl_data.at[row_start + 1, 0]
        hours_df["pay_period"] = f"{HISTORICAL_HOURS_YEAR}-{pp_num:02d}"

        # Transform
        # ---------
        # Sum overtime/double and premium hours all into overtime_hrs
        hours_df["overtime_hrs"] = hours_df["ot_hrs"] + hours_df["premium_hrs"]

        # Interpret NaN as 0 hrs for regular and overtime hours
        hours_df["reg_hrs"] = hours_df["reg_hrs"].fillna(0)
        hours_df["overtime_hrs"] = hours_df["overtime_hrs"].fillna(0)

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
                    "pay_period",
                    "dept_wd_id",
                    "dept_name",
                    "reg_hrs",
                    "overtime_hrs",
                    "prod_hrs",
                    "nonprod_hrs",
                    "total_hrs",
                    "total_fte",
                ]
            ]
        )

    # Join all the tables and calculate the start date for each pay period number
    df = pd.concat(ret)
    df = add_pay_period_start_date(df)
    return df


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
        hours_df.columns.values[2] = "reg_hrs"
        hours_df.columns.values[3] = "CALLBK - CALLBACK"
        hours_df.columns.values[4] = "DBLTME - DOUBLETIME"
        hours_df.columns.values[6] = "OT_1.5 - OVERTIME"

        # Drop next row, which are sub-headers. Find columns by name, because there are
        # a couple different formats with different columns orders.
        hours_df = hours_df.loc[1:]

        # Read year and pay period number from file name
        year_pp_num = re.search(r"PP#(\d+) (\d+) ", file, re.IGNORECASE)
        year = year_pp_num.group(2)
        pp_num = int(year_pp_num.group(1))
        hours_df["pay_period"] = f"{year}-{pp_num:02d}"

        # Transform
        # ---------
        # Sum overtime/double and premium hours all into overtime_hrs
        hours_df["overtime_hrs"] = (
            hours_df["CALLBK - CALLBACK"]
            + hours_df["DBLTME - DOUBLETIME"]
            + hours_df["OT_1.5 - OVERTIME"]
        )

        # Add a new column "dept_wd_id" using dict, and drop rows without a known workday dept ID
        hours_df["dept_wd_id"] = (
            hours_df["Department Name"]
            .str.lower()
            .map({k.lower(): v for k, v in ALIASES_TO_WDID.items()})
        )
        hours_df.dropna(subset=["dept_wd_id"], inplace=True)
        # Reassign canonical dept names from workday ID using dict
        hours_df["dept_name"] = hours_df["dept_wd_id"].map(WDID_TO_DEPT_NAME)

        # Rename and specific relevant columns to retain
        hours_df.rename(
            columns={
                "Regular Hours": "reg_hrs",
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
                    "pay_period",
                    "dept_wd_id",
                    "dept_name",
                    "reg_hrs",
                    "overtime_hrs",
                    "prod_hrs",
                    "nonprod_hrs",
                    "total_hrs",
                    "total_fte",
                ]
            ]
        )

    # Join all the tables and calculate the start date for each pay period number
    df = pd.concat(ret)
    df = add_pay_period_start_date(df)
    return df


def add_pay_period_start_date(df):
    """
    Return a dataframe that adds a start_date column that translates the pay_period column
    into the first day of the pay period
    """

    def find_start_date_of_first_pay_period_in_year(year):
        # If needed, walk the anchor date back by 2 weeks increments until anchor is in a prior to target year.
        # PAY_PERIOD_ANCHOR_DATE["start_date"] is the start date of pay period #1 in the year PAY_PERIOD_ANCHOR_DATE["year"].
        # It is likely a date in Dec of the previous year.
        cur_date = PAY_PERIOD_ANCHOR_DATE["start_date"]
        if year < PAY_PERIOD_ANCHOR_DATE["year"]:
            while year <= cur_date.year:
                cur_date += timedelta(days=-14)

        # For accounting, find the first pay period that include at least one day in the year.  Walk forward from the anchor
        # start_date 14 days at a time. Once the period end date (13 days from start date) is in the target year, we have
        # the dates for the first pay period.
        #
        # This is different than pay roll pay periods, where pay period 1 is numbered to correspond to the first pay date
        # in the year. The pay date for a pay period is the Friday following the end of the pay period
        while cur_date.year <= year:
            end_date = cur_date + timedelta(days=13)
            if end_date.year == year:
                return cur_date
            cur_date += timedelta(days=14)

    # Get the year range of pay_period data
    min_year, _pp_num = map(int, df["pay_period"].min().split("-"))
    max_year, _pp_num = map(int, df["pay_period"].max().split("-"))

    # Calculate start dates for every pay period in the year range found above
    pay_period_to_start_date = {}
    for year in range(min_year, max_year + 1):
        cur_date = find_start_date_of_first_pay_period_in_year(year)
        pay_period = 1
        while True:
            # End date is the Friday 2 weeks from the start of the pay period
            end_date = cur_date + timedelta(days=13)

            # If the pay date is in a future year, we're done with this year
            if end_date.year > year:
                break

            # Note the start date of this pay period and advanced 2 weeks to the next period
            pay_period_to_start_date[f"{year:04d}-{pay_period:02d}"] = cur_date
            cur_date += timedelta(days=14)
            pay_period += 1

    # Make a copy of the data that includes a start_date column
    df = df.copy()
    df["start_date"] = df["pay_period"].map(pay_period_to_start_date)
    return df


def transform_hours_pay_periods_to_months(hours_df: pd.DataFrame):
    """
    Translates hours data from pay periods in the format to the equivalent values by months
    """

    def copy_data_part(df_row, data, date, factor):
        """
        Copy column values from a data frame row, df_row, to a dict, data.
        Values are multiplied by factor, which represents the part of the original data
        that belongs to a particular year and month (specified by date).
        """
        month = f"{date.year:04d}-{date.month:02d}"
        row_id = f"{df_row['dept_wd_id']}; {month}"
        data[row_id] = data.get(row_id, {})
        data_row = data[row_id]
        data_row["month"] = month
        data_row["dept_wd_id"] = df_row["dept_wd_id"]
        data_row["dept_name"] = df_row["dept_name"]
        for col in [
            "reg_hrs",
            "overtime_hrs",
            "prod_hrs",
            "nonprod_hrs",
            "total_hrs",
        ]:
            # Multiply the pay period value by portion of the period in this month
            data_row[col] = data_row.get(col, 0) + df_row[col] * factor

        # FTE has to be recalculated using a conversion factor of (14 days / days in month),
        # because the FTE depends on the total hours / number of total days
        days_in_month = calendar.monthrange(date.year, date.month)[1]
        data_row["total_fte"] = data_row.get("total_fte", 0) + df_row[
            "total_fte"
        ] * factor * (14 / days_in_month)

    # Map the rows in the per-pay-period data to per-month rows
    data = {}
    for _idx, df_row in hours_df.iterrows():
        start_date = df_row["start_date"]
        end_date = start_date + timedelta(days=13)

        # Calculate the proportion of the pay period in the start_date month
        # monthrange() returns weekday of first day of the month and number of days in month
        days_in_start_month = calendar.monthrange(start_date.year, start_date.month)[1]
        factor = min(1.0, (days_in_start_month - start_date.day + 1) / 14)

        # Add values from data columns to the current row with index: (dept ID, month)
        copy_data_part(df_row, data, start_date, factor)

        # If the end month is different, then do the same thing with the rest of the pay period
        if start_date.month != end_date.month:
            copy_data_part(df_row, data, end_date, 1 - factor)

    ret = pd.DataFrame(data).T
    return ret.reset_index(drop=True)


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
    db = create_engine(f"sqlite:///{TMP_DB_FILE}", echo=SHOW_SQL_IN_LOG)
    create_schema(db)
    logging.info(f"Created tables in {TMP_DB_FILE}")

    # Extract and perform basic transformation of data from spreadsheets
    volumes_df = read_volume_data(VOLUMES_FILE, VOLUMES_SHEET)
    budget_df = read_budget_data(VOLUMES_FILE, VOLUMES_BUDGET_SHEET)
    income_stmt_df = read_income_stmt_data(income_stmt_files)
    historical_hours_df = read_historical_hours_and_fte_data(HISTORICAL_HOURS_FILE)
    hours_by_pay_period_df = read_hours_and_fte_data(hours_files)
    hours_by_pay_period_df = pd.concat([historical_hours_df, hours_by_pay_period_df])

    # Transform hours data to months
    hours_by_month_df = transform_hours_pay_periods_to_months(hours_by_pay_period_df)

    # Load data into DB. Clear each table prior to loading from dataframe
    with Session(db) as session:
        clear_table_and_insert_data(session, Volume, volumes_df)
        clear_table_and_insert_data(session, Budget, budget_df)
        clear_table_and_insert_data(session, HoursByPayPeriod, hours_by_pay_period_df)
        clear_table_and_insert_data(session, Hours, hours_by_month_df)
        clear_table_and_insert_data(session, IncomeStmt, income_stmt_df)

    # Update last ingest time and modified times for source data files
    update_meta(db, source_files)

    # Move new database in place
    db.dispose()
    os.replace(TMP_DB_FILE, DEFAULT_DB_FILE)
