import os
import pathlib
from dotenv import load_dotenv
from prefect import flow, task
from prefect_shell import ShellOperation
from prefect_aws import AwsCredentials, S3Bucket
from prefect.blocks.system import Secret

# Load environment from .env file, does not overwrite existing env variables
load_dotenv()

# Load config from env vars
PRH_DASH_SOURCE_DIR = os.environ.get("PRH_DASH_SOURCE_DIR")
PRH_DASH_CLOUDFLARE_R2_URL = os.environ.get("PRH_DASH_CLOUDFLARE_R2_URL")
PRH_DASH_CLOUDFLARE_R2_BUCKET = os.environ.get("PRH_DASH_CLOUDFLARE_R2_BUCKET")

# Update path to include worker user's local bin
os.environ["PATH"] = f"{os.environ['PATH']}:{pathlib.Path.home()}/.local/bin"


@task
def run_task():
    data_key = Secret.load("prh-dash-data-key").get()
    aws_creds = AwsCredentials.load("cloudflare-r2-dataset")
    s3_bucket = S3Bucket(bucket_name="dataset", credentials=aws_creds)

    with ShellOperation(
        commands=[
            "pipenv install",
            f'pipenv run python ingest.py "{PRH_DASH_SOURCE_DIR}" -o db.sqlite3',
            f"pipenv run python src/encrypt.py -key {data_key} -encrypt db.sqlite3 -out db.sqlite3.enc",
        ],
        stream_output=True,
    ) as op:
        proc = op.trigger()
        proc.wait_for_completion()
        if proc.return_code != 0:
            raise Exception(f"Failed, exit code {proc.return_code}")

    # Upload encrypted output file to S3
    out = s3_bucket.upload_from_path("db.sqlite3.enc", "prh-dash.db.sqlite3.enc")
    print("Uploaded to S3:", out)


@flow(retries=0, retry_delay_seconds=300)
def prh_dash_ingest():
    run_task()


if __name__ == "__main__":
    prh_dash_ingest()
