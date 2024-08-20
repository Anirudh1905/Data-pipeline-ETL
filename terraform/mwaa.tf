resource "aws_s3_bucket" "mwaa_bucket" {
  bucket_prefix = "mwaa-bucket-"
}

resource "aws_s3_bucket_versioning" "bucket_versioning" {
  bucket = aws_s3_bucket.mwaa_bucket.id
  versioning_configuration {
    status = "Enabled"
  }
}


resource "aws_mwaa_environment" "mwaa_env" {
  name                 = "mwaa-environment"
  environment_class    = "mw1.small"
  execution_role_arn   = aws_iam_role.mwaa_role.arn
  source_bucket_arn    = aws_s3_bucket.mwaa_bucket.arn
  dag_s3_path          = "dags/"
  requirements_s3_path = "requirements.txt"

  network_configuration {
    security_group_ids = [aws_security_group.mwaa_sg.id]
    subnet_ids         = [aws_subnet.private-us-east-1a.id, aws_subnet.private-us-east-1b.id]
  }

  webserver_access_mode = "PUBLIC_ONLY"

  logging_configuration {
    dag_processing_logs {
      enabled   = true
      log_level = "INFO"
    }
    scheduler_logs {
      enabled   = true
      log_level = "INFO"
    }
    task_logs {
      enabled   = true
      log_level = "INFO"
    }
    webserver_logs {
      enabled   = true
      log_level = "INFO"
    }
    worker_logs {
      enabled   = true
      log_level = "INFO"
    }
  }
}

resource "aws_security_group" "mwaa_sg" {
  name        = "mwaa-sg"
  description = "Security group for MWAA"
  vpc_id      = aws_vpc.vpc.id

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}