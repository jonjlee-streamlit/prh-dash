import logging
import pandas as pd
from ...util import df_get_val_or_range
from ...RawData import RawData


def parse(filename: str, contents: bytes, excel_sheets: list[str]) -> RawData:
    # Detect if incoming file is for this department
    if filename.endswith(".xlsx"):
        df = pd.read_excel(contents, sheet_name=0, header=None)
    if not _is_income_stmt_file(df, excel_sheets):
        return None

    logging.info(f"Using Radiology parser for {filename}")

    # Get all rows through row with no value in first column
    first_empty_row = df.iloc[, 0].isna().idxmax()
    income_stmt = df.iloc[ : first_empty_row-1, 0:16]

    return RawData(income_statements=[income_stmt])


def _is_income_stmt_file(df, excel_sheets):
    """
    Detect if valid income statement file:
    - Excel file with exactly 1 worksheet prefixed with "FIN"
    - cell A2 contains "Ledger Account"
    """
    if not (len(excel_sheets) == 1 and excel_sheets[0].startswith("FIN")):
        return False
    return df.iloc[1, 0] == "Ledger Account"
