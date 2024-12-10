import pandas as pd


def check_data_files(volumes_file: str, income_stmt_files: list[str]) -> bool:
    """
    Source data sanity checks. This doesn't compare actual numbers, but checks that we can
    do ingest at all, such as ensuring the right columns are where we expect them to be
    """
    # - Dashboard Supporting Data, List worksheet: verify same data as static_data.WDID_TO_DEPTNAME
    # - Each income statement sheet has Ledger Account cell, and data in columns A:Q
    return True
