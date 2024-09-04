# Create a Dead Letter Queue (DLQ)
resource "aws_sqs_queue" "my_dlq" {
  name = "training-queue-dlq"
}

# Create an SQS queue
resource "aws_sqs_queue" "my_queue" {
  name = "training-queue"
  visibility_timeout_seconds = 900
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.my_dlq.arn
    maxReceiveCount     = 5
  })
}
