from datetime import timedelta
import json
import logging
from fastapi import APIRouter, HTTPException
from fastapi.encoders import jsonable_encoder
import redis
import boto3
from constants import DATABASE_URL, REDIS_HOST, REDIS_PORT, STREAM_NAME
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from data_schema import ChurnData, ResponseModel, TelecomUsers, Base

redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)
kinesis_client = boto3.client("kinesis", region_name="us-east-1")
data_router = APIRouter(prefix="/data")

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
Base.metadata.create_all(engine, checkfirst=True)
CACHE_EXPIRATION_TIME = timedelta(days=1)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@data_router.post("/ingest")
async def send_data(user: ChurnData) -> ResponseModel:
    """
    Ingest user data and send it to an AWS Kinesis stream.

    This endpoint ingests user data, sends it to an AWS Kinesis stream, and caches the data in Redis.
    If the data is already cached, it returns a response indicating that the data is already in the stream.
    If the data is successfully sent to the stream, it updates the cache.

    Args:
        user (ChurnData): The user churn data to be ingested.

    Returns:
        ResponseModel: A response model containing the status, cache status, and response data.
    """
    redis_key_id = f"user:{user.customerID}:{user.gender}:{user.SeniorCitizen}:{user.Partner}:{user.Dependents}:{user.tenure}:{user.PhoneService}:{user.MultipleLines}:{user.InternetService}:{user.OnlineSecurity}"
    cached_data = redis_client.get(redis_key_id)

    if cached_data:
        return ResponseModel(
            status="Success", cached=True, response={"result": "Data already in stream"}
        )

    response = kinesis_client.put_record(
        StreamName=STREAM_NAME,
        Data=json.dumps(user.dict()),
        PartitionKey=str(user.customerID),
    )

    if response["ResponseMetadata"]["HTTPStatusCode"] != 200:
        return ResponseModel(
            status="Failed",
            cached=False,
            response={"result": "Failed to add data to stream"},
        )

    redis_client.delete(redis_key_id)
    redis_client.set(
        redis_key_id,
        json.dumps(user.dict()),
        ex=int(CACHE_EXPIRATION_TIME.total_seconds()),
    )

    return ResponseModel(
        status="Success", cached=False, response={"result": "Data added to stream"}
    )


@data_router.get("/list_users")
async def list_users(limit: int) -> ResponseModel:
    """
    Retrieve a list of users from the TelecomUsers table.

    This endpoint fetches a limited number of users from the TelecomUsers table in the database.
    If users are found, it returns a ResponseModel with the user data.
    If no users are found, it returns a ResponseModel indicating failure.
    In case of an exception, it raises an HTTP 500 error.

    Args:
        limit (int): The maximum number of users to retrieve.

    Returns:
        ResponseModel: A response model containing the status, cache status, and response data.
    """
    session = Session()
    try:
        users = session.query(TelecomUsers).limit(limit).all()
        if users:
            return ResponseModel(
                status="Success", cached=False, response=jsonable_encoder(users)
            )
        return ResponseModel(
            status="Failed",
            cached=False,
            response={"Detail": "TelecomUsers table not found"},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()
