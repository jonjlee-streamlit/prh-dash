import logging
import pandas as pd
from ...util import df_get_val_or_range, df_next_empty_row, df_get_tables_by_columns
from ...RawData import RawData


def parse(filename: str, contents: bytes, excel_sheets: list[str]) -> RawData:
    # Detect if incoming file is for this department
    if filename.endswith(".xlsx"):
        df = pd.read_excel(contents, sheet_name=0, header=None)

    income_stmt_file = _is_income_stmt_file(df, excel_sheets)
    volumes_file = _is_volumes_file(df, excel_sheets)

    if not (income_stmt_file or volumes_file):
        return None

    logging.info(f"Using Radiology parser for {filename}")

    if income_stmt_file:
        # Entire sheet is income statement
        return RawData(income_statements=[df])
    elif volumes_file:
        # Historical volumes
        volumes = list(df_get_tables_by_columns(df, "6:14"))
        return RawData(rads_volumes=volumes)

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
