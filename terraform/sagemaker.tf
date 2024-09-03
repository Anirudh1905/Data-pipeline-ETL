resource "aws_s3_bucket" "model_bucket" {
  bucket_prefix = "model-bucket-"
}

# resource "aws_security_group" "sagemaker_sg" {
#   name        = "sagemaker_sg"
#   description = "Allow inbound traffic"
#   vpc_id      = aws_vpc.vpc.id

#   ingress {
#     from_port   = 0
#     to_port     = 65535
#     protocol    = "tcp"
#     security_groups = [aws_eks_cluster.cluster.vpc_config[0].cluster_security_group_id]
#   }

#   egress {
#     from_port   = 0
#     to_port     = 0
#     protocol    = "-1"
#     cidr_blocks = ["0.0.0.0/0"]
#   }

#   tags = {
#     Name = "sagemaker-sg"
#   }
# }

# IAM Role for SageMaker
resource "aws_iam_role" "sagemaker_role" {
  name = "sagemaker-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "sagemaker.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "sagemaker_full_access" {
  role       = aws_iam_role.sagemaker_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSageMakerFullAccess"
}

resource "aws_iam_role_policy_attachment" "sagemaker_s3_access" {
  role       = aws_iam_role.sagemaker_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3FullAccess"
}

# resource "aws_vpc_endpoint" "s3" {
#   vpc_id            = aws_vpc.vpc.id
#   service_name      = "com.amazonaws.us-east-1.s3"
#   route_table_ids   = [
#     aws_route_table.private_1.id,
#     aws_route_table.private_2.id
#   ]
# }

# # SageMaker Model
# resource "aws_sagemaker_model" "model" {
#   name                 = "telecom-churn-model"
#   execution_role_arn   = aws_iam_role.sagemaker_role.arn
#   primary_container {
#     image = "683313688378.dkr.ecr.us-east-1.amazonaws.com/sagemaker-scikit-learn:0.23-1-cpu-py3"
#     model_data_url    = "s3://${aws_s3_bucket.model_bucket.bucket}/model.tar.gz"
#   }
#   vpc_config {
#     subnets            = [aws_subnet.private-us-east-1a.id, aws_subnet.private-us-east-1b.id]
#     security_group_ids = [aws_security_group.sagemaker_sg.id]
#   }
# }

# # SageMaker Endpoint Configuration
# resource "aws_sagemaker_endpoint_configuration" "endpoint_config" {
#   name = "sagemaker-endpoint-config"

#   production_variants {
#     variant_name           = "AllTraffic"
#     model_name             = aws_sagemaker_model.model.name
#     initial_instance_count = 1
#     instance_type          = "ml.m4.xlarge"
#     initial_variant_weight = 1.0
#   }
# }

# # SageMaker Endpoint
# resource "aws_sagemaker_endpoint" "endpoint" {
#   name = "sagemaker-endpoint"
#   endpoint_config_name = aws_sagemaker_endpoint_configuration.endpoint_config.name
#   depends_on = [aws_sagemaker_model.model]
# }

output "sagemaker_role_arn" {
  description = "The ARN of the SageMaker IAM role"
  value       = aws_iam_role.sagemaker_role.arn
}

# output "sagemaker_endpoint_config_name" {
#   description = "The name of the SageMaker endpoint configuration"
#   value       = aws_sagemaker_endpoint_configuration.endpoint_config.name
# }