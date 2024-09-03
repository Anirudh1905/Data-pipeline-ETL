import json
import tarfile
import boto3
import os
import logging

sagemaker = boto3.client("sagemaker")
sqs = boto3.client("sqs")
s3 = boto3.client("s3")

MAX_CONCURRENT_JOBS = 20
QUEUE_URL = os.environ["SQS_QUEUE_URL"]
DLQ_URL = os.environ["DLQ_URL"]
MODEL_BUCKET_NAME = os.environ["MODEL_BUCKET_NAME"]
ROLE_ARN = os.environ["SAGEMAKER_ROLE_ARN"]


def lambda_handler(event, context):
    """
    AWS Lambda function to manage SageMaker training jobs.

    This function checks the number of currently running SageMaker training jobs and starts new ones
    if there is available capacity. It polls messages from an SQS queue, each containing information
    about a training job to start. If a training job starts successfully, the message is deleted from
    the queue. If it fails, the message is sent to a dead-letter queue (DLQ).

    Args:
        event (dict): The event data passed to the Lambda function.
        context (object): The context in which the Lambda function is called.

    Returns:
        dict: A response object containing the status code and a message.
    """
    print("Event:", event)
    # Get the number of currently running training jobs
    response = sagemaker.list_training_jobs(StatusEquals="InProgress")
    running_jobs = len(response["TrainingJobSummaries"])
    available_capacity = MAX_CONCURRENT_JOBS - running_jobs

    print(f"Running jobs: {running_jobs}")
    print(f"Available capacity: {available_capacity}")

    # Check if we can start a new training job
    if available_capacity > 0:
        # Poll a message from the SQS queue
        messages_list = []
        while available_capacity > 0:
            messages = sqs.receive_message(
                QueueUrl=QUEUE_URL,
                MaxNumberOfMessages=min(10, available_capacity),
                WaitTimeSeconds=20,
            )
            if "Messages" in messages:
                messages_list.extend(messages["Messages"])
                available_capacity -= len(messages["Messages"])
            else:
                print("No messages in the queue")
                break

        print("Number of messages: ", len(messages_list))
        results = []
        for message in messages_list:
            receipt_handle = message["ReceiptHandle"]
            body = json.loads(message["Body"])
            input_s3_path = body["s3_path"]
            training_job_name = body["training_job_name"]
            response = sagemaker_train(training_job_name, input_s3_path)
            if response["ResponseMetadata"]["HTTPStatusCode"] == 200:
                results.append(
                    {
                        "training_job_name": training_job_name,
                        "status": "started successfully",
                    }
                )
            else:
                logging.error(f"Failed to start training job {training_job_name}")
                sqs.send_message(QueueUrl=DLQ_URL, MessageBody=json.dumps(message))
                results.append(
                    {
                        "training_job_name": training_job_name,
                        "status": "failed to start",
                    }
                )
            sqs.delete_message(QueueUrl=QUEUE_URL, ReceiptHandle=receipt_handle)

        return {"statusCode": 200, "body": json.dumps(results)}
    else:
        return {"statusCode": 200, "body": json.dumps("Concurrency limit reached")}


def sagemaker_train(training_job_name, trainpath):
    """
    Create and start a SageMaker training job.

    This function creates a tarball of the training script, uploads it to S3, and then starts
    a SageMaker training job using the specified training data path.

    Args:
        training_job_name (str): The name of the training job.
        trainpath (str): The S3 path to the training data.

    Returns:
        dict: The response from the SageMaker create_training_job API call.
    """
    source = "/tmp/source.tar.gz"  # Use /tmp directory
    try:
        with tarfile.open(source, "w:gz") as tar:
            tar.add("train.py")
    except Exception as e:
        print(f"Error creating tar file: {e}")
        raise

    try:
        s3.upload_file(source, MODEL_BUCKET_NAME, f"{training_job_name}/source.tar.gz")
    except Exception as e:
        print(f"Error uploading to S3: {e}")
        raise

    try:
        response = sagemaker.create_training_job(
            TrainingJobName=training_job_name,
            HyperParameters={
                "sagemaker_program": "train.py",
                "sagemaker_submit_directory": f"s3://{MODEL_BUCKET_NAME}/{training_job_name}/source.tar.gz",
            },
            AlgorithmSpecification={
                "TrainingImage": "683313688378.dkr.ecr.us-east-1.amazonaws.com/sagemaker-scikit-learn:1.2-1-cpu-py3",
                "TrainingInputMode": "File",
            },
            RoleArn=ROLE_ARN,
            InputDataConfig=[
                {
                    "ChannelName": "train",
                    "DataSource": {
                        "S3DataSource": {
                            "S3DataType": "S3Prefix",
                            "S3Uri": trainpath,
                            "S3DataDistributionType": "FullyReplicated",
                        }
                    },
                }
            ],
            OutputDataConfig={"S3OutputPath": f"s3://{MODEL_BUCKET_NAME}/"},
            ResourceConfig={
                "InstanceType": "ml.c5.xlarge",
                "InstanceCount": 1,
                "VolumeSizeInGB": 10,
            },
            StoppingCondition={"MaxRuntimeInSeconds": 86400},
            EnableNetworkIsolation=False,
        )
        return response
    except Exception as e:
        print(f"Error creating SageMaker training job: {e}")
        raise
