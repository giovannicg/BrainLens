variable "aws_region" {
  type        = string
  description = "AWS region"
  default     = "eu-north-1"
}

variable "project" {
  type        = string
  description = "Project name prefix"
  default     = "brainlens"
}

variable "mongo_url" {
  type        = string
  description = "MongoDB connection string"
}

variable "bedrock_model_id" {
  type        = string
  default     = "amazon.nova-lite-v1:0"
}

variable "vlm_timeout" {
  type    = number
  default = 300
}


