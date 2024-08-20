from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from airflow.providers.postgres.hooks.postgres import PostgresHook
from datetime import datetime, timedelta
import json
import logging

# Define default arguments for the DAG
default_args = {
    "owner": "anirudh",
    "depends_on_past": False,
    "start_date": datetime(2024, 1, 1),
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

BUCKET_NAME = "app-stream-data-20240812123628897900000002"
AWS_CONN_ID = "aws_default"
POSTGRES_CONN_ID = "rds_default"

# Define the DAG
dag = DAG(
    "s3_to_rds",
    default_args=default_args,
    description="A DAG to parse S3 bucket, transform data, and store in RDS PostgreSQL",
    schedule_interval="@daily",
    catchup=False,
)


# Function to recursively list and read S3 objects, and transform the data
def read_transform_store_data(**kwargs):

    s3_hook = S3Hook(aws_conn_id=AWS_CONN_ID)

    def list_keys_recursive(bucket, prefix=""):
        keys = []
        kwargs = {"Bucket": bucket, "Prefix": prefix}
        while True:
            resp = s3_hook.get_conn().list_objects_v2(**kwargs)
            if "Contents" in resp:
                for obj in resp["Contents"]:
                    # Filter objects modified in the last 24 hours
                    if obj["LastModified"] > datetime.now(
                        obj["LastModified"].tzinfo
                    ) - timedelta(hours=24):
                        keys.append(obj["Key"])
            if "NextContinuationToken" in resp:
                kwargs["ContinuationToken"] = resp["NextContinuationToken"]
            else:
                break
        return keys

    keys = list_keys_recursive(BUCKET_NAME)

    logging.info(f"Found {len(keys)} objects in the S3 bucket")
    all_records = []

    for key in keys:
        obj = s3_hook.get_key(key, BUCKET_NAME)
        data = obj.get()["Body"].read().decode("utf-8")

        # Split the data into individual JSON objects
        records = data.split("}{")
        records = [
            record + "}" if not record.endswith("}") else record for record in records
        ]
        records = [
            "{" + record if not record.startswith("{") else record for record in records
        ]

        # Collect all records
        all_records.extend(records)

    pg_hook = PostgresHook(postgres_conn_id=POSTGRES_CONN_ID)
    conn = pg_hook.get_conn()
    cursor = conn.cursor()

    for record in all_records:
        json_data = json.loads(record)
        upsert_query = """
        INSERT INTO "Users" (id, name)
        VALUES (%s, %s)
        ON CONFLICT (id) DO UPDATE SET
        name = EXCLUDED.name;
        """
        cursor.execute(upsert_query, (json_data["id"], json_data["name"]))
        conn.commit()

    cursor.close()
    conn.close()


etl_task = PythonOperator(
    task_id="read_transform_store_data",
    provide_context=True,
    python_callable=read_transform_store_data,
    dag=dag,
)

etl_task
