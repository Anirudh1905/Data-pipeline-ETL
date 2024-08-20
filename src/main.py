from fastapi import Depends, FastAPI, HTTPException
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
app = FastAPI()


@app.get("/")
async def read_root():
    return RedirectResponse(url="/docs")


@app.post("/create_user")
async def send_data(user: DataModel) -> ResponseModel:

    redis_key_id = f"user:{user.id}:{user.name}"
    cached_data = redis_client.get(redis_key_id)
    # redis_client.delete(f"user:{user.id}")

    if cached_data:
        return ResponseModel(
            status="Success", cached=True, response=json.loads(cached_data)
        )

    response = kinesis_client.put_record(
        StreamName=STREAM_NAME, Data=json.dumps(user.dict()), PartitionKey=str(user.id)
    )

    redis_client.set(redis_key_id, json.dumps(user.dict()))

    return ResponseModel(status="Success", cached=False, response=response)


@app.get("/users/{user_id}")
async def read_user(user_id: int) -> ResponseModel:
    redis_key_id = f"user:{user_id}"
    cached_user = redis_client.get(redis_key_id)

    if cached_user:
        return ResponseModel(
            status="Success", cached=True, response=json.loads(cached_user)
        )
    session = Session()
    try:
        user = session.query(Users).filter(Users.id == user_id).first()
        if user:
            response_dict = {}
            response_dict["id"], response_dict["name"] = user.id, user.name
            return ResponseModel(status="Success", cached=False, response=response_dict)
        return ResponseModel(
            status="Failed", cached=False, response={"Detail": "User not found"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()


@app.get("/users")
async def read_users() -> ResponseModel:
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
