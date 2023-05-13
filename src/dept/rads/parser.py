import logging
import pandas as pd
from ...util import df_get_range
from ...RawData import RawData

def parse(filename: str, contents: bytes, excel_sheets: list[str]) -> RawData:
    # Detect if incoming file is for this department:
    # - Excel file with exactly 1 worksheet prefixed with "FIN"
    # - Is an income statement file - ie. cell A2 contains "Ledger Account"
    if not (len(excel_sheets) == 1 and excel_sheets[0].startswith("FIN") and (_is_income_stmt_file(contents))):
        return None
    
    logging.info(f"Using Radiology parser for {filename}")

    return None

def _is_income_stmt_file(contents: bytes): 
    df = pd.read_excel(contents, sheet_name=0, header=None)
    return df.iloc[1, 0] == "Ledger Account"
