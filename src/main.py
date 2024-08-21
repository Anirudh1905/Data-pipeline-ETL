from datetime import timedelta
from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import redis
import boto3
import json
import logging

from constants import DATABASE_URL, REDIS_HOST, STREAM_NAME, REDIS_PORT
from schema import Base, DataModel, Users, ResponseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)
kinesis_client = boto3.client("kinesis", region_name="us-east-1")
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
Base.metadata.create_all(engine, checkfirst=True)
CACHE_EXPIRATION_TIME = timedelta(days=1)
app = FastAPI()


@app.get("/")
async def read_root():
    """
    Redirect to the API documentation.

    This endpoint redirects the root URL to the FastAPI documentation page.

    Returns:
        RedirectResponse: A response that redirects to the /docs URL.
    """
    return RedirectResponse(url="/docs")


@app.post("/create_user")
async def send_data(user: DataModel) -> ResponseModel:
    """
    Create a new user and send data to Kinesis stream.

    This endpoint creates a new user, sends the user data to an AWS Kinesis stream,
    and caches the user data in Redis. If the user data is already cached, it returns
    the cached data.

    Args:
        user (DataModel): The user data to be created and sent.

    Returns:
        ResponseModel: A response model containing the status, cache status, and response data.
    """
    redis_key_id = f"user:{user.id}:{user.name}"
    cached_data = redis_client.get(redis_key_id)

    if cached_data:
        return ResponseModel(
            status="Success", cached=True, response={"result": "Data already in stream"}
        )

    response = kinesis_client.put_record(
        StreamName=STREAM_NAME, Data=json.dumps(user.dict()), PartitionKey=str(user.id)
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


@app.get("/users")
async def read_users() -> ResponseModel:
    """
    Retrieve all users from the database.

    This endpoint fetches all users from the Users table in the database.
    If users are found, it returns a ResponseModel with a dictionary of user IDs and names.
    If no users are found, it returns a ResponseModel indicating failure.
    In case of an exception, it raises an HTTP 500 error.

    Returns:
        ResponseModel: A response model containing the status, cache status, and response data.
    """
    session = Session()
    try:
        users = session.query(Users).all()
        if users:
            response_dict = {}
            for user in users:
                response_dict[user.id] = user.name

            return ResponseModel(status="Success", cached=False, response=response_dict)
        return ResponseModel(
            status="Failed", cached=False, response={"Detail": "Users table not found"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
