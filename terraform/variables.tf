variable "region" {
  description = "The AWS region to deploy resources in."
  type        = string
  default     = "us-east-1"
}

variable "name" {
  description = "Airflow Env name"
  type        = string
  default     = "mwaa-environment"
}

variable "account_id" {
  description = "The AWS account ID where resources will be deployed."
  type        = string
}

variable "kms_key_arn" {
  description = "The ARN of the KMS key to be used by MWAA."
  type        = string
  default     = null
}
