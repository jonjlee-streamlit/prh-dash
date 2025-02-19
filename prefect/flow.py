import os
from dotenv import load_dotenv
from prefect import flow, task
from prefect_shell import ShellOperation
from prefect_aws import AwsCredentials, S3Bucket
from prefect.blocks.system import Secret

PREFECT_FLOW_NAME = "prw-datamart-finance"

# Load env vars from a .env file
# load_dotenv() does NOT overwrite existing env vars that are set before running this script.
# Look for the .env file in this file's directory
# Actual .env file (eg .env.dev) depends on value of PRW_ENV. Default to prod.
PRW_ENV = os.getenv("PRW_ENV", "prod")
ENV_FILES = {
    "dev": ".env.dev",
    "prod": ".env.prod",
}
ENV_PATH = os.path.join(os.path.dirname(__file__), ENV_FILES.get(PRW_ENV))
print(f"Using environment: {ENV_PATH}")
load_dotenv(dotenv_path=ENV_PATH)

# Load config from env vars into constants
PRW_DB_ODBC = os.environ.get("PRW_DB_ODBC") or Secret.load("prw-db-url").get()
PRH_FINANCE_VENV_NAME = os.environ.get("PRH_FINANCE_VENV_NAME", "")
PRH_FINANCE_CLOUDFLARE_R2_BUCKET = os.environ.get("PRH_FINANCE_CLOUDFLARE_R2_BUCKET")
PRH_FINANCE_DATA_KEY = (
    os.environ.get("PRH_FINANCE_DATA_KEY") or Secret.load("prh-dash-data-key").get()
)
PRH_FINANCE_ENCRYPTED_DB_FILE = os.environ.get("PRH_FINANCE_ENCRYPTED_DB_FILE")
PRH_FINANCE_ENCRYPTED_JSON_FILE = os.environ.get("PRH_FINANCE_ENCRYPTED_JSON_FILE")


@task
def upload_files(bucket_name, files):
    """Upload the given files to S3"""
    aws_creds = AwsCredentials.load("cloudflare-r2-dataset")
    s3_bucket = S3Bucket(bucket_name=bucket_name, credentials=aws_creds)
    for file in files:
        s3_bucket.upload_from_path(file, file)
    print("Uploaded to S3:", files)


@flow(
    retries=0,
    name=PREFECT_FLOW_NAME + (f"{PRW_ENV}." if PRW_ENV != "prod" else ""),
)
def prh_datamart_finance():
    # Set working dir to path of this file
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    print("Running from:", os.getcwd())

    with ShellOperation(
        commands=[
            "pipenv install",
            f"pipenv run python ingest_datamart.py --prw {PRW_DB_ODBC} --db {PRH_FINANCE_ENCRYPTED_DB_FILE} --kv {PRH_FINANCE_ENCRYPTED_JSON_FILE} --key {PRH_FINANCE_DATA_KEY}",
        ],
        env={
            "PIPENV_IGNORE_VIRTUALENVS": "1",
            "PIPENV_CUSTOM_VENV_NAME": PRH_FINANCE_VENV_NAME,
        },
        stream_output=True,
    ) as op:
        proc = op.trigger()
        proc.wait_for_completion()
        if proc.return_code != 0:
            raise Exception(f"Failed, exit code {proc.return_code}")

    # Upload encrypted output to S3
    if PRH_FINANCE_CLOUDFLARE_R2_BUCKET:
        upload_files(
            PRH_FINANCE_CLOUDFLARE_R2_BUCKET,
            [PRH_FINANCE_ENCRYPTED_DB_FILE, PRH_FINANCE_ENCRYPTED_JSON_FILE],
        )


if __name__ == "__main__":
    prh_datamart_finance()
