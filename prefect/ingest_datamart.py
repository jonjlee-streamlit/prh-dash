import sys
import os
import shutil
import argparse
import json
import pandas as pd
from sqlalchemy import create_engine, select, text
from cryptography.fernet import Fernet
from prefect.blocks.system import Secret

# Add project root to PYTHONPATH so we can import from src/
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from src.model import Base


def encrypt_file(file: str, outfile: str, key: str):
    """Encrypts the given file and writes the output to disk"""
    fernet = Fernet(key)
    with open(file, "rb") as f:
        data = f.read()
        encrypted = fernet.encrypt(data)
    with open(outfile, "wb") as f:
        f.write(encrypted)


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Ingest data from PRW warehouse to datamart."
    )
    parser.add_argument(
        "--prw", help="PRW warehouse ODBC connection string", required=True
    )
    parser.add_argument("--db", help="Output database file path", required=True)
    parser.add_argument("--kv", help="Output key/value data file path", required=True)
    parser.add_argument("--key", help="Encryption key")
    return parser.parse_args()


def main():
    args = parse_arguments()
    prw_db_url = args.prw
    output_db_file = args.db
    output_kv_file = args.kv
    encrypt_key = args.key
    tmp_db_file = "datamart.sqlite3"
    tmp_kv_file = "datamart.json"

    TABLE_MAP = {
        "prw_volumes": "volumes",
        "prw_uos": "uos",
        "prw_budget": "budget",
        "prw_hours": "hours",
        "prw_contracted_hours": "contracted_hours",
        "prw_hours_by_pay_period": "hours_by_pay_period",
        "prw_income_stmt": "income_stmt",
    }

    # Create the sqlite output database and create the tables as defined in ../src/model.py
    db_engine = create_engine(f"sqlite:///{tmp_db_file}")
    Base.metadata.create_all(db_engine)

    # Read each table from PRW warehouse (MSSQL in prod, sqlite in dev) and write into the equivalent table using the same column names
    prw_engine = create_engine(prw_db_url)
    for source_table, dest_table in TABLE_MAP.items():
        # Read data from source
        query = f"SELECT * FROM {source_table}"
        df = pd.read_sql(query, prw_engine)

        # Write to destination
        df.to_sql(dest_table, db_engine, if_exists="replace", index=False)
        print(f"Transferred {len(df)} rows from {source_table}")

    # Read the contracted_hours_updated_month column from the first row in table
    # prw_contracted_hours_meta. Use sqlalchemy since source DB can be MSSQL or sqlite.
    query = (
        select(text("contracted_hours_updated_month"))
        .select_from(text("prw_contracted_hours_meta"))
        .limit(1)
    )
    with prw_engine.connect() as connection:
        result = connection.execute(query).scalar()

    # Write the result to the output JSON file
    with open(tmp_kv_file, "w") as f:
        json.dump({"contracted_hours_updated_month": result}, f)

    # Finally encrypt output files
    if encrypt_key and encrypt_key.lower() != "none":
        encrypt_file(tmp_db_file, output_db_file, encrypt_key)
        encrypt_file(tmp_kv_file, output_kv_file, encrypt_key)
    else:
        # Copy files to output paths if no encryption key is provided
        shutil.copy(tmp_db_file, output_db_file)
        shutil.copy(tmp_kv_file, output_kv_file)


if __name__ == "__main__":
    main()
