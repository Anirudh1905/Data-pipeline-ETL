from datetime import datetime
import io
import json
import logging
import tarfile
from fastapi import APIRouter, HTTPException
import joblib
import pandas as pd
import redis

from sqlalchemy import create_engine
import boto3
from constants import (
    DATABASE_URL,
    MODEL_BUCKET_NAME,
    REDIS_CACHE_PREFIX,
    REDIS_HOST,
    REDIS_PORT,
    SQS_QUEUE_URL,
)
from data_schema import (
    ChurnData,
    InferenceRequest,
    InferenceResponse,
    StatusRequest,
    StatusResponse,
    TrainRequest,
    TrainResponse,
)

sagemaker_client = boto3.client("sagemaker", region_name="us-east-1")
sqs_client = boto3.client("sqs", region_name="us-east-1")
s3_client = boto3.client("s3", region_name="us-east-1")
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)

model_router = APIRouter(prefix="/model")
engine = create_engine(DATABASE_URL)


@model_router.post("/train")
async def train(request: TrainRequest) -> TrainResponse:
    """
    Initiate a training job for the model.

    This endpoint initiates a training job for the model. If no S3 path is provided,
    it fetches data from the database, uploads it to S3, and then sends a message to
    an SQS queue to start the training job.

    Args:
        request (TrainRequest): The request containing the S3 path for training data which is optional.

    Returns:
        TrainResponse: A response indicating the status of the training job initiation.
    """
    try:
        training_job_name = "training-job-name-" + datetime.now().strftime(
            "%Y-%m-%d-%H-%M-%S"
        )
        if request.s3_path is None:
            logging.info("No S3 path provided. Fetching data from the database.")
            query = 'SELECT * FROM "TelecomUsers"'
            df = pd.read_sql(query, engine)
            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=False)
            s3_key = f"{training_job_name}/data/input.csv"
            s3_client.put_object(
                Bucket=MODEL_BUCKET_NAME, Key=s3_key, Body=csv_buffer.getvalue()
            )
            s3_path = f"s3://{MODEL_BUCKET_NAME}/{s3_key}"
            request.s3_path = s3_path

        request_dict = request.dict()
        request_dict["training_job_name"] = training_job_name

        message_body = json.dumps(request_dict)
        sqs_client.send_message(QueueUrl=SQS_QUEUE_URL, MessageBody=message_body)

        return TrainResponse(
            message=f"Training job {training_job_name} request submitted successfully."
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@model_router.post("/status")
async def status(request: StatusRequest) -> StatusResponse:
    """
    Check the status of a training job.

    This endpoint checks the status of a training job using the SageMaker client.

    Args:
        request (StatusRequest): The request containing the training job name.

    Returns:
        StatusResponse: A response indicating the status of the training job.
    """
    try:
        response = sagemaker_client.describe_training_job(
            TrainingJobName=request.training_job_name
        )
        return StatusResponse(training_job_status=response["TrainingJobStatus"])
    except Exception as e:
        return StatusResponse(training_job_status=f"Training not started yet {str(e)}")


@model_router.post("/inference")
async def inference(request: InferenceRequest) -> InferenceResponse:
    """
    Perform inference using the trained model.

    This endpoint performs inference using the trained model. It checks if the model
    and transformer are cached in Redis. If not, it downloads them from S3, caches them,
    and then uses them to make predictions.

    Args:
        request (InferenceRequest): The request containing the training job name and input data.

    Returns:
        InferenceResponse: A response containing the predictions.
    """
    try:
        cache_key_model = f"{REDIS_CACHE_PREFIX}{request.training_job_name}:model"
        cache_key_transformer = (
            f"{REDIS_CACHE_PREFIX}{request.training_job_name}:transformer"
        )

        # Check if the model and transformer are in the cache
        model_bytes = redis_client.get(cache_key_model)
        transformer_bytes = redis_client.get(cache_key_transformer)

        if model_bytes is None or transformer_bytes is None:
            # Download the model.tar.gz file from S3 into memory
            model_tar_key = f"{request.training_job_name}/output/model.tar.gz"
            response = s3_client.get_object(Bucket=MODEL_BUCKET_NAME, Key=model_tar_key)
            model_tar_data = response["Body"].read()

            # Extract the contents of the tarball in memory
            with tarfile.open(fileobj=io.BytesIO(model_tar_data), mode="r:gz") as tar:
                # Extract model.joblib
                model_file = tar.extractfile("model.joblib")
                if model_file:
                    model = joblib.load(model_file)
                    model_bytes = io.BytesIO()
                    joblib.dump(model, model_bytes)
                    model_bytes.seek(0)
                    redis_client.set(cache_key_model, model_bytes.getvalue())
                    logging.info("Model loaded and cached successfully")
                else:
                    raise FileNotFoundError("Model file not found in tarball")

                # Extract transformer.joblib
                transformer_file = tar.extractfile("transformer.joblib")
                if transformer_file:
                    transformer = joblib.load(transformer_file)
                    transformer_bytes = io.BytesIO()
                    joblib.dump(transformer, transformer_bytes)
                    transformer_bytes.seek(0)
                    redis_client.set(
                        cache_key_transformer, transformer_bytes.getvalue()
                    )
                    logging.info("Transformer loaded and cached successfully")
                else:
                    raise FileNotFoundError("Transformer file not found in tarball")
        else:
            # Deserialize the model and transformer from the cache
            model = joblib.load(io.BytesIO(model_bytes))
            transformer = joblib.load(io.BytesIO(transformer_bytes))
            logging.info("Model and transformer loaded from cache")

        df = pd.DataFrame([data.dict() for data in request.input_data])
        X = transformer.transform(df)
        y_pred = model.predict(X)
        prediction = y_pred.tolist()

        response_list = []
        for i, data in enumerate(request.input_data):
            response_list.append(ChurnData(**data.model_dump(), Churn=prediction[i]))

        return InferenceResponse(prediction=response_list)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
