
variable "project" {
  type        = string
  description = "Project name prefix"
  default     = "brainlens"
}

# Legacy AWS variables (for backward compatibility)
variable "aws_region" {
  type        = string
  description = "AWS region"
  default     = "eu-north-1"
}

variable "mongo_url" {
  type        = string
  description = "MongoDB connection string"
  default     = ""
}

variable "bedrock_model_id" {
  type        = string
  default     = "amazon.nova-lite-v1:0"
}

variable "vlm_timeout" {
  type    = number
  default = 300
}

# EKS Configuration
variable "eks_node_count" {
  type        = number
  description = "Number of EKS nodes"
  default     = 3
}

variable "eks_instance_type" {
  type        = string
  description = "EKS node instance type"
  default     = "t3.medium"
}


