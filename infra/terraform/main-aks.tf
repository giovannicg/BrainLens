# Amazon EKS Configuration for BrainLens
# AWS Kubernetes Service setup

terraform {
  backend "s3" {
    bucket         = "brainlens-terraform-state-1758055280"  # Reemplaza con tu bucket
    key            = "brainlens/terraform.tfstate"
    region         = "eu-north-1"
    dynamodb_table = "brainlens-terraform-locks"
    encrypt        = true
  }
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

locals {
  name = var.project
}

# VPC for EKS
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true
  tags = {
    Name = "${local.name}-vpc"
  }
}

resource "aws_subnet" "public_a" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = "${var.aws_region}a"
  map_public_ip_on_launch = true
  tags = {
    Name = "${local.name}-public-a"
  }
}

resource "aws_subnet" "public_b" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.2.0/24"
  availability_zone       = "${var.aws_region}b"
  map_public_ip_on_launch = true
  tags = {
    Name = "${local.name}-public-b"
  }
}

resource "aws_internet_gateway" "igw" {
  vpc_id = aws_vpc.main.id
  tags = {
    Name = "${local.name}-igw"
  }
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.igw.id
  }

  tags = {
    Name = "${local.name}-public-rt"
  }
}

resource "aws_route_table_association" "a" {
  subnet_id      = aws_subnet.public_a.id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "b" {
  subnet_id      = aws_subnet.public_b.id
  route_table_id = aws_route_table.public.id
}

# EKS Cluster
resource "aws_eks_cluster" "brainlens" {
  name     = "${local.name}-eks"
  role_arn = aws_iam_role.eks_cluster.arn
  version  = "1.30"

  vpc_config {
    subnet_ids = [aws_subnet.public_a.id, aws_subnet.public_b.id]
  }

  depends_on = [
    aws_iam_role_policy_attachment.eks_cluster_policy,
    aws_iam_role_policy_attachment.eks_service_policy,
  ]

  tags = {
    Name = "${local.name}-eks"
  }
}

# EKS Node Group
resource "aws_eks_node_group" "brainlens" {
  cluster_name    = aws_eks_cluster.brainlens.name
  node_group_name = "${local.name}-node-group"
  node_role_arn   = aws_iam_role.eks_nodes.arn
  subnet_ids      = [aws_subnet.public_a.id, aws_subnet.public_b.id]

  scaling_config {
    desired_size = 1
    max_size     = 1
    min_size     = 1
  }

  # Usar un tipo disponible y económico
  instance_types = ["t3.medium"]
  capacity_type  = "SPOT"

  depends_on = [
    aws_iam_role_policy_attachment.eks_worker_node_policy,
    aws_iam_role_policy_attachment.eks_cni_policy,
    aws_iam_role_policy_attachment.eks_container_registry_policy,
  ]

  tags = {
    Name = "${local.name}-node-group"
  }
}

# IAM Roles for EKS
resource "aws_iam_role" "eks_cluster" {
  name = "${local.name}-eks-cluster-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "eks.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "eks_cluster_policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSClusterPolicy"
  role       = aws_iam_role.eks_cluster.name
}

resource "aws_iam_role_policy_attachment" "eks_service_policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSServicePolicy"
  role       = aws_iam_role.eks_cluster.name
}

resource "aws_iam_role" "eks_nodes" {
  name = "${local.name}-eks-node-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "eks_worker_node_policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy"
  role       = aws_iam_role.eks_nodes.name
}

resource "aws_iam_role_policy_attachment" "eks_cni_policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy"
  role       = aws_iam_role.eks_nodes.name
}

resource "aws_iam_role_policy_attachment" "eks_container_registry_policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
  role       = aws_iam_role.eks_nodes.name
}

# ECR Repositories
resource "aws_ecr_repository" "frontend" {
  name                 = "${local.name}-frontend"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}

resource "aws_ecr_repository" "auth" {
  name                 = "${local.name}-auth"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}

resource "aws_ecr_repository" "image" {
  name                 = "${local.name}-image"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}

resource "aws_ecr_repository" "annotation" {
  name                 = "${local.name}-annotation"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}

resource "aws_ecr_repository" "colab" {
  name                 = "${local.name}-colab"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}

# MongoDB Atlas (external managed service)
# No Terraform resources needed - configure via MongoDB Atlas UI
# Use the connection string from MongoDB Atlas in your Kubernetes secrets

# S3 Bucket for file storage
resource "aws_s3_bucket" "storage" {
  bucket = "${local.name}-storage-${random_string.bucket_suffix.result}"

  tags = {
    Name = "${local.name}-storage"
  }
}

resource "aws_s3_bucket_versioning" "storage" {
  bucket = aws_s3_bucket.storage.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "random_string" "bucket_suffix" {
  length  = 8
  lower   = true
  upper   = false
  numeric = true
  special = false
}

# CloudWatch Logs
resource "aws_cloudwatch_log_group" "eks" {
  name              = "/aws/eks/${local.name}/cluster"
  retention_in_days = 30
}

# Outputs
output "eks_cluster_name" {
  value = aws_eks_cluster.brainlens.name
}

output "eks_cluster_endpoint" {
  value = aws_eks_cluster.brainlens.endpoint
}

# MongoDB Atlas outputs (configure manually)
output "mongodb_atlas_info" {
  value = {
    connection_string = "Configure in MongoDB Atlas UI and update Kubernetes secrets"
    database_name     = "brainlens"
    note              = "Use the connection string from MongoDB Atlas dashboard"
  }
  description = "MongoDB Atlas connection information"
}

output "s3_bucket_name" {
  value = aws_s3_bucket.storage.bucket
}

output "ecr_repository_urls" {
  value = {
    frontend    = aws_ecr_repository.frontend.repository_url
    auth        = aws_ecr_repository.auth.repository_url
    image       = aws_ecr_repository.image.repository_url
    annotation  = aws_ecr_repository.annotation.repository_url
    colab       = aws_ecr_repository.colab.repository_url
  }
}