import os
import asyncio
from datetime import datetime
from dotenv import load_dotenv
from prefect import flow, task
from prefect_shell import ShellOperation
from prefect_aws import AwsCredentials, S3Bucket
from prefect.blocks.system import Secret


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
PRH_DASH_VENV_NAME = os.environ.get("PRH_DASH_VENV_NAME")
PRH_DASH_SOURCE_DIR = os.environ.get("PRH_DASH_SOURCE_DIR")
PRH_DASH_CLOUDFLARE_R2_URL = os.environ.get("PRH_DASH_CLOUDFLARE_R2_URL")
PRH_DASH_CLOUDFLARE_R2_BUCKET = os.environ.get("PRH_DASH_CLOUDFLARE_R2_BUCKET")
PRH_DASH_ENCRYPTED_DB_FILE = os.environ.get("PRH_DASH_ENCRYPTED_DB_FILE")

# Temporary output file
TMP_OUTPUT_DB = "db.sqlite3"


def get_flow_name():
    base_name = "prw-datamart-finance-dash"
    env_prefix = f"{PRW_ENV}." if PRW_ENV != "prod" else ""
    return f"{env_prefix}{base_name}"


@flow(retries=0, retry_delay_seconds=300, name=get_flow_name())
def prh_dash_ingest():
    # Set working dir to project root
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    print("Running from:", os.getcwd())

    data_key = (Secret.load("prh-dash-data-key")).get()
    aws_creds = AwsCredentials.load("cloudflare-r2-dataset")

    with ShellOperation(
        commands=[
            "pipenv install",
            f'pipenv run python ingest.py "{PRH_DASH_SOURCE_DIR}" -o {TMP_OUTPUT_DB}',
            f"pipenv run python src/encrypt.py -key {data_key} -encrypt {TMP_OUTPUT_DB} -out {PRH_DASH_ENCRYPTED_DB_FILE}",
        ],
        env={"PIPENV_CUSTOM_VENV_NAME": PRH_DASH_VENV_NAME},
        stream_output=True,
    ) as op:
        proc = op.trigger()
        proc.wait_for_completion()
        if proc.return_code != 0:
            raise Exception(f"Failed, exit code {proc.return_code}")

    # Upload encrypted output file to S3
    s3_bucket = S3Bucket(
        bucket_name=PRH_DASH_CLOUDFLARE_R2_BUCKET, credentials=aws_creds
    )
    out = s3_bucket.upload_from_path(
        PRH_DASH_ENCRYPTED_DB_FILE, PRH_DASH_ENCRYPTED_DB_FILE
    )
    print("Uploaded to S3:", out)


if __name__ == "__main__":
    prh_dash_ingest()
