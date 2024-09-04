# Create an IAM role for the Lambda function
resource "aws_iam_role" "lambda_role" {
  name               = "lambda-execution-role"
  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      }
    }
  ]
}
EOF
}

# Attach the AWSLambdaBasicExecutionRole policy to the role
resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Attach a custom policy for SQS access to the role
resource "aws_iam_policy" "sqs_access_policy" {
  name        = "sqs-access-policy"
  description = "Policy to allow Lambda to access SQS"
  policy      = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "sqs:ReceiveMessage",
      "Resource": "${aws_sqs_queue.my_queue.arn}"
    },
    {
      "Effect": "Allow",
      "Action": "sqs:DeleteMessage",
      "Resource": "${aws_sqs_queue.my_queue.arn}"
    },
    {
      "Effect": "Allow",
      "Action": "sqs:GetQueueAttributes",
      "Resource": "${aws_sqs_queue.my_queue.arn}"
    }
  ]
}
EOF
}

resource "aws_iam_role_policy_attachment" "sqs_access_attachment" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = aws_iam_policy.sqs_access_policy.arn
}

# Attach a custom policy for S3 access to the role
resource "aws_iam_policy" "s3_access_policy" {
  name        = "s3-access-policy"
  description = "Policy to allow Lambda to access S3"
  policy      = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::${aws_s3_bucket.model_bucket.id}",
        "arn:aws:s3:::${aws_s3_bucket.model_bucket.id}/*"
      ]
    }
  ]
}
EOF
}

resource "aws_iam_role_policy_attachment" "s3_access_attachment" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = aws_iam_policy.s3_access_policy.arn
}

# Attach a custom policy for SageMaker access to the role
resource "aws_iam_policy" "sagemaker_access_policy" {
  name        = "sagemaker-access-policy"
  description = "Policy to allow Lambda to launch SageMaker training jobs"
  policy      = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "sagemaker:CreateTrainingJob",
        "sagemaker:DescribeTrainingJob",
        "sagemaker:StopTrainingJob",
        "sagemaker:ListTrainingJobs"
      ],
      "Resource": "*"
    }
  ]
}
EOF
}

resource "aws_iam_role_policy_attachment" "sagemaker_access_attachment" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = aws_iam_policy.sagemaker_access_policy.arn
}

# Create a Lambda function
resource "aws_lambda_function" "my_lambda" {
  filename         = "lambda.zip" # Path to your deployment package
  function_name    = "train_lambda_function"
  role             = aws_iam_role.lambda_role.arn
  handler          = "lambda_processor.lambda_handler"
  runtime          = "python3.11" # Change runtime as needed
  source_code_hash = filebase64sha256("lambda.zip")
  timeout          = 30

  environment {
    variables = {
      SQS_QUEUE_URL = aws_sqs_queue.my_queue.url
      DLQ_URL = aws_sqs_queue.my_dlq.url
      MODEL_BUCKET_NAME = aws_s3_bucket.model_bucket.bucket
      SAGEMAKER_ROLE_ARN = aws_iam_role.sagemaker_role.arn
    }
  }
}

resource "aws_lambda_event_source_mapping" "sqs_trigger" {
  event_source_arn  = aws_sqs_queue.my_queue.arn
  function_name     = aws_lambda_function.my_lambda.arn
  batch_size        = 10
  enabled           = true
}

output "sqs_url" {
  value = aws_sqs_queue.my_queue.url
}

output "dlq_url" {
  value = aws_sqs_queue.my_dlq.url
}