import io
import logging
import tarfile
import boto3
from fastapi import HTTPException
import joblib
import pandas as pd
from sagemaker.sklearn.estimator import SKLearn
from sagemaker.inputs import TrainingInput

from src.data_schema import InferenceRequest
from src.routers.model import status
from src.trainer.lambda_processor import sagemaker_train


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

s3 = boto3.client("s3")
sagemaker = boto3.client("sagemaker")

s3_folder = "s3://model-bucket-20240826061620914100000001/"
MODEL_BUCKET_NAME = "model-bucket-20240826061620914100000001"
ROLE_ARN = "arn:aws:iam::765826404413:role/sagemaker-role"
input_s3_path = "s3://model-bucket-20240826061620914100000001/test/input.csv"


def train():
    sklearn_estimator = SKLearn(
        entry_point="train.py",
        source_dir=".",
        role=ROLE_ARN,
        instance_count=1,
        instance_type="ml.m5.large",
        output_path=s3_folder,
        framework_version="1.2-1",
        py_version="py3",
    )

    train_input = TrainingInput(s3_data=input_s3_path, content_type="csv")
    sklearn_estimator.fit({"train": train_input})


def inference(request: InferenceRequest):
    try:
        model_tar_key = f"{request.training_job_name}/output/model.tar.gz"
        response = s3.get_object(Bucket=MODEL_BUCKET_NAME, Key=model_tar_key)
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
                # redis_client.set(cache_key_model, model_bytes.getvalue())
                logger.info("Model loaded and cached successfully")
            else:
                raise FileNotFoundError("Model file not found in tarball")

            # Extract transformer.joblib
            transformer_file = tar.extractfile("transformer.joblib")
            if transformer_file:
                transformer = joblib.load(transformer_file)
                transformer_bytes = io.BytesIO()
                joblib.dump(transformer, transformer_bytes)
                transformer_bytes.seek(0)
                # redis_client.set(cache_key_transformer, transformer_bytes.getvalue())
                logger.info("Transformer loaded and cached successfully")
            else:
                raise FileNotFoundError("Transformer file not found in tarball")

        df = pd.DataFrame([data.dict() for data in request.input_data])
        X = transformer.transform(df)
        y_pred = model.predict(X)
        prediction = y_pred.tolist()

        return prediction
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


input_data = [
    {
        "customerID": "7590-VHVEG",
        "gender": "Female",
        "SeniorCitizen": "0",
        "Partner": "Yes",
        "Dependents": "No",
        "tenure": "1",
        "PhoneService": "No",
        "MultipleLines": "No phone service",
        "InternetService": "DSL",
        "OnlineSecurity": "No",
        "OnlineBackup": "Yes",
        "DeviceProtection": "No",
        "TechSupport": "No",
        "StreamingTV": "No",
        "StreamingMovies": "No",
        "Contract": "Month-to-month",
        "PaperlessBilling": "Yes",
        "PaymentMethod": "Electronic check",
        "MonthlyCharges": "29.85",
        "TotalCharges": "29.85",
    },
    {
        "customerID": "5575-GNVDE",
        "gender": "Male",
        "SeniorCitizen": "0",
        "Partner": "No",
        "Dependents": "No",
        "tenure": "34",
        "PhoneService": "Yes",
        "MultipleLines": "No",
        "InternetService": "DSL",
        "OnlineSecurity": "Yes",
        "OnlineBackup": "No",
        "DeviceProtection": "Yes",
        "TechSupport": "No",
        "StreamingTV": "No",
        "StreamingMovies": "No",
        "Contract": "One year",
        "PaperlessBilling": "No",
        "PaymentMethod": "Mailed check",
        "MonthlyCharges": "56.95",
        "TotalCharges": "1889.5",
    },
]


train()
sagemaker_train("test", "s3://model-bucket-20240826061620914100000001/test/input.csv")

print(status("training-job-name-2024-09-03-13-19-43"))

inference_result = inference(
    InferenceRequest(training_job_name="xyzz18", input_data=input_data)
)
print(inference_result)