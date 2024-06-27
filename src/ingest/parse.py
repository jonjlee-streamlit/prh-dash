import re
import logging
import pandas as pd
from datetime import datetime, timedelta
from .. import util, static_data


# Starting point for converting bi-weekly pay period number to start and end dates. Set to the start date of pay period 1 for the given year.
# Pay periods go from Saturday -> Friday two weeks later, and the pay date is on the Friday following the pay period.
PAY_PERIOD_ANCHOR_DATE = {
    "year": 2023,
    "start_date": datetime(2022, 12, 17),
}


def read_volume_and_uos_data(filename, sheet):
    """
    Read the Excel sheet with volume data into a dataframe
    """
    # Read tables from excel worksheet
    logging.info(f"Reading {filename}, {sheet}")
    xl_data = pd.read_excel(filename, sheet_name=sheet, header=None)
    volumes_by_year = util.df_get_tables_by_columns(xl_data, "1:70")

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

    # Store map of dept ID to volume unit, which is in column C of the first table
    tbl = volumes_by_year[0]
    dept_id_to_unit = {row[0]: row[2] for row in tbl.itertuples(index=False)}

    data = []
    for df in volumes_by_year:
        # The first table has an extra column for the volume units (eg Patient Days or Tests). The remainder do not.
        # Look for year in row 2, column 3. If it's not there, then we have an extra column
        year_row, year_col = 0, 2
        col_offset = 0 if pd.notna(df.iloc[year_row, year_col]) else 1
        year = df.iloc[year_row, year_col + col_offset]
        assert pd.notna(year)

        # Skip header rows x 2 with year and month names
        df = df.iloc[2:]

        # Pull volume data from each row
        for _index, row in df.iterrows():
            # Dept ID and name in the A:B
            dept_wd_id = row.iloc[0]
            dept_name = row.iloc[1]

            # Volume unit for this dept
            unit = dept_id_to_unit.get(dept_wd_id, None)

            # Iterate over volume numbers in columns C:N. enumerate(..., start=1) results in month = [1..12]
            # Most tables have two non-data columns preceding data. col_offset above gives us the number of
            # extra non-data columns in this table
            volumes = row.iloc[2 + col_offset : 2 + col_offset + 12]
            for month_num, volume in enumerate(volumes, start=1):
                if pd.notnull(volume):
                    # Format month column like "2022-01"
                    month = f"{year:04d}-{month_num:02d}"
                    data.append([dept_wd_id, dept_name, month, volume, unit])

    return pd.DataFrame(
        data, columns=["dept_wd_id", "dept_name", "month", "volume", "unit"]
    )


def read_budget_data(filename, budget_sheet, hrs_per_volume_sheet):
    """
    Read the sheet from the Dashboard Supporting Data Excel workbook with budgeted hours and volume data into a dataframe
    """
    # Extract table and assign column names that match DB schema for columns we will retain
    logging.info(f"Reading {filename}, {budget_sheet}")
    xl_data = pd.read_excel(filename, sheet_name=budget_sheet, header=None)
    budget_df = util.df_get_tables_by_rows(
        xl_data, cols="B:K", start_row_idx=6, limit=1
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
        "",
        "hourly_rate",
        "Current YTD FTE",
    ]

    logging.info(f"Reading {filename}, {hrs_per_volume_sheet}")
    xl_data = pd.read_excel(filename, sheet_name=hrs_per_volume_sheet, header=None)
    hrs_per_volume_df = util.df_get_table(xl_data, start_cell="A2", has_header_row=True)

    # Transform
    # ---------
    # Drop columns without an Workday ID
    budget_df.dropna(subset=["dept_wd_id"], inplace=True)
    # Join volumes and budgeted hours tables based on workday ID
    budget_df = budget_df.join(hrs_per_volume_df.set_index("ID"), on="dept_wd_id")
    # Interpret NaN as 0 budgeted fte, hours, volume and hrs/volume
    budget_df["budget_fte"] = budget_df["budget_fte"].fillna(0)
    budget_df["budget_prod_hrs"] = budget_df["budget_prod_hrs"].fillna(0)
    budget_df["budget_volume"] = budget_df["budget_volume"].fillna(0)
    budget_df["budget_prod_hrs_per_volume"] = budget_df["GOAL"].fillna(0)
    budget_df["hourly_rate"] = budget_df["hourly_rate"].fillna(0)

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
            .map({k.lower(): v for k, v in static_data.ALIASES_TO_WDID.items()})
        )
        unrecognized = (
            income_stmt_df[income_stmt_df["dept_wd_id"].isna()]
            .loc[:, "Cost Center"]
            .unique()
        )
        income_stmt_df.dropna(subset=["dept_wd_id"], inplace=True)
        income_stmt_df["dept_name"] = income_stmt_df["dept_wd_id"].map(
            static_data.WDID_TO_DEPT_NAME
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


def read_historical_hours_and_fte_data(filename, year):
    """
    Read historical hours/FTE data from the custom formatted Excel workbook
    """
    # Extract data from first and only worksheet
    logging.info(f"Reading {filename}")
    xl_data = pd.read_excel(filename, header=None, usecols="A,B,C,D,G,M,N,AB")

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
            "overtime_hrs",
            "prod_hrs",
            "nonprod_hrs",
            "total_hrs",
            "total_fte",
        ]

        # Add the pay period number in the format YYYY-##
        pp_num = xl_data.at[row_start + 1, 0]
        pp_end_date = xl_data.at[row_start + 1, 1]
        hours_df["pay_period"] = f"{year}-{pp_num:02d}"

        # Transform
        # ---------
        # Interpret NaN as 0 hrs for regular and overtime hours and total FTE
        hours_df["reg_hrs"] = hours_df["reg_hrs"].fillna(0)
        hours_df["overtime_hrs"] = hours_df["overtime_hrs"].fillna(0)
        hours_df["total_fte"] = hours_df["total_fte"].fillna(0)

        # Add a new column "dept_wd_id" using dict, and drop rows without a known workday dept ID
        hours_df["dept_wd_id"] = (
            hours_df["Department Name"]
            .str.lower()
            .map({k.lower(): v for k, v in static_data.ALIASES_TO_WDID.items()})
        )
        hours_df.dropna(subset=["dept_wd_id"], inplace=True)
        # Reassign canonical dept names from workday ID using dict
        hours_df["dept_name"] = hours_df["dept_wd_id"].map(
            static_data.WDID_TO_DEPT_NAME
        )

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
    df = _add_pay_period_start_date(df)
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
            hours_df["DBLTME - DOUBLETIME"] + hours_df["OT_1.5 - OVERTIME"]
        )

        # Add a new column "dept_wd_id" using dict, and drop rows without a known workday dept ID
        hours_df["dept_wd_id"] = (
            hours_df["Department Name"]
            .str.lower()
            .map({k.lower(): v for k, v in static_data.ALIASES_TO_WDID.items()})
        )
        hours_df.dropna(subset=["dept_wd_id"], inplace=True)
        # Reassign canonical dept names from workday ID using dict
        hours_df["dept_name"] = hours_df["dept_wd_id"].map(
            static_data.WDID_TO_DEPT_NAME
        )

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
    df = _add_pay_period_start_date(df)
    return df


def _add_pay_period_start_date(df):
    """
    Return a dataframe that adds a start_date column that translates the pay_period column
    into the first day of the pay period
    """
    # Get the year range of pay_period data
    min_year, _pp_num = map(int, df["pay_period"].min().split("-"))
    max_year, _pp_num = map(int, df["pay_period"].max().split("-"))

    # Calculate start dates for every pay period in the year range found above
    pay_period_to_start_date = {}
    for year in range(min_year, max_year + 1):
        cur_date = _find_start_date_of_first_pay_period_in_year(year)
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


def _find_start_date_of_first_pay_period_in_year(year):
    # The pay date for a pay period, which starts on Sunday, is the Friday following the end of the pay period.
    # Pay date = end date + 7 days = start date + 13 days + 7 days
    def calc_pay_date(start_date):
        return start_date + timedelta(days=20)

    # If needed, walk back from anchor date by 2 weeks increments until the pay period pay date is in a prior year to target year.
    # PAY_PERIOD_ANCHOR_DATE["start_date"] is the start date of pay period #1 in the year PAY_PERIOD_ANCHOR_DATE["year"].
    # It is likely in Dec of the previous year.
    cur_date = PAY_PERIOD_ANCHOR_DATE["start_date"]
    if year < PAY_PERIOD_ANCHOR_DATE["year"]:
        while year <= calc_pay_date(cur_date).year:
            cur_date += timedelta(days=-14)

    # The first pay period is the first pay day within a year. A pay period's pay date is 1 week past the end of the period.
    # For example, pay 2023 PP#1 has dates of 12/17/22-12/30/22 with a pay date of 1/6/23. Since 1/6/23 is the first pay date
    # in 2023, it is pay period #1.
    #
    # Walk forward from the anchor start_date 14 days at a time. Once the pay date (end date + 7 days = 20 days from start date)
    # is in the target year, we have the dates for the first pay period.
    #
    while cur_date.year <= year:
        pay_date = calc_pay_date(cur_date)
        if pay_date.year == year:
            return cur_date
        cur_date += timedelta(days=14)
