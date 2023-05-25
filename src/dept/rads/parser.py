import logging
import pandas as pd
from ...util import df_get_tables_by_columns, df_get_tables_by_rows
from ...RawData import RawData

KNOWN_RADS_DEPT_NUMBERS = ["CC_71200", "CC_71300", "CC_71400", "CC_71430", "CC_71450", "CC_71600"]

def parse(filename: str, contents: bytes, excel_sheets: list[str]) -> RawData:
    # Detect if incoming file is for this department
    if filename.endswith(".xlsx"):
        df = pd.read_excel(contents, sheet_name=0, header=None)

    income_stmt_file = _is_income_stmt_file(df, excel_sheets)
    volumes_file = _is_volumes_file(df, excel_sheets)
    hours_file = _is_hours_file(df, excel_sheets)

    if not (income_stmt_file or volumes_file or hours_file):
        return None

    logging.info(f"{filename} - using Radiology parser")

    if income_stmt_file:
        # Entire sheet is income statement
        return RawData(income_statements=[df])
    elif volumes_file:
        # Historical volumes
        volumes = list(df_get_tables_by_columns(df, "6:14"))
        return RawData(rads_volumes=volumes)
    elif hours_file:
        # Productive and non-productive hours
        sheet2 = pd.read_excel(contents, sheet_name=1, header=None)
        hours_by_pay_period = list(df_get_tables_by_rows(df, "A:S", start_row_idx=4))
        hours_by_month = list(df_get_tables_by_rows(sheet2, "A:R", start_row_idx=3))
        return RawData(hours_by_pay_period=hours_by_pay_period, hours_by_month=hours_by_month)

    return None


def _is_income_stmt_file(df, excel_sheets):
    """
    Detect if valid income statement file:
    - Excel file with exactly 1 worksheet prefixed with "FIN"
    - cell A2 contains "Ledger Account"
    """
    if not (len(excel_sheets) == 1 and excel_sheets[0].startswith("FIN")):
        return False
    return df.iloc[1, 0] == "Ledger Account"


def _is_volumes_file(df, excel_sheets):
    """
    Detect if valid historic volumes file:
    - Excel file with exactly 1 worksheet containing "dBase"
    - cell D4 contains "STAT REPORT CARD"
    """
    if not (len(excel_sheets) == 1 and "dBase" in excel_sheets[0]):
        return False
    return df.iloc[3, 3] == "STAT REPORT CARD"

def _is_hours_file(df, excel_sheets):
    """
    Detect if valid hours report file:
    - Excel file with exactly 2 worksheets
    - First worksheet is for pay periods. A8 should contain a recognized rads department number
    """
    if not len(excel_sheets) == 2:
        return False
    return df.iloc[7, 0] in KNOWN_RADS_DEPT_NUMBERS