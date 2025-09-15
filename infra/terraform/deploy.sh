#!/bin/bash

# BrainLens Production Deployment Script
# This script deploys the infrastructure and builds/pushes Docker images

set -e

echo "🚀 Starting BrainLens Production Deployment"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="brainlens"
AWS_REGION="eu-north-1"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

echo -e "${YELLOW}Project:${NC} $PROJECT_NAME"
echo -e "${YELLOW}Region:${NC} $AWS_REGION"
echo -e "${YELLOW}Account ID:${NC} $ACCOUNT_ID"

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo -e "\n${YELLOW}Checking prerequisites...${NC}"

if ! command_exists aws; then
    echo -e "${RED}Error: AWS CLI is not installed${NC}"
    exit 1
fi

if ! command_exists docker; then
    echo -e "${RED}Error: Docker is not installed${NC}"
    exit 1
fi

if ! command_exists terraform; then
    echo -e "${RED}Error: Terraform is not installed${NC}"
    exit 1
fi

# Check AWS credentials
if ! aws sts get-caller-identity >/dev/null 2>&1; then
    echo -e "${RED}Error: AWS credentials are not configured${NC}"
    exit 1
fi

echo -e "${GREEN}Prerequisites check passed${NC}"

# Navigate to terraform directory
cd "$(dirname "$0")"

# Initialize Terraform
echo -e "\n${YELLOW}Initializing Terraform...${NC}"
terraform init

# Validate Terraform configuration
echo -e "\n${YELLOW}Validating Terraform configuration...${NC}"
terraform validate

# Plan the deployment
echo -e "\n${YELLOW}Planning Terraform deployment...${NC}"
terraform plan -out=tfplan

# Ask for confirmation
echo -e "\n${YELLOW}Review the plan above. Do you want to proceed with the deployment? (y/N)${NC}"
read -r response
if [[ ! "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    echo "Deployment cancelled"
    exit 0
fi

# Apply the deployment
echo -e "\n${YELLOW}Applying Terraform deployment...${NC}"
terraform apply tfplan

# Get ECR repository URLs
echo -e "\n${YELLOW}Getting ECR repository information...${NC}"
FRONTEND_REPO=$(terraform output -raw ecr_frontend_uri)
IMAGE_REPO=$(terraform output -raw ecr_image_uri)
AUTH_REPO=$(terraform output -raw ecr_auth_uri)
COLAB_REPO=$(terraform output -raw ecr_colab_uri)
ANNOTATION_REPO=$(terraform output -raw ecr_annotation_uri)
ALB_DNS=$(terraform output -raw alb_dns)

echo -e "${GREEN}ECR Repositories:${NC}"
echo "Frontend: $FRONTEND_REPO"
echo "Image: $IMAGE_REPO"
echo "Auth: $AUTH_REPO"
echo "Colab: $COLAB_REPO"
echo "Annotation: $ANNOTATION_REPO"
echo "ALB DNS: $ALB_DNS"

# Authenticate Docker with ECR
echo -e "\n${YELLOW}Authenticating Docker with ECR...${NC}"
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

# Build and push Docker images
echo -e "\n${YELLOW}Building and pushing Docker images...${NC}"

# Function to build and push image
build_and_push() {
    local service_name=$1
    local repo_url=$2
    local dockerfile_path=$3

    echo -e "${YELLOW}Building $service_name...${NC}"
    docker build -t $service_name:latest $dockerfile_path

    echo -e "${YELLOW}Tagging $service_name...${NC}"
    docker tag $service_name:latest $repo_url:latest

    echo -e "${YELLOW}Pushing $service_name...${NC}"
    docker push $repo_url:latest

    echo -e "${GREEN}$service_name pushed successfully${NC}"
}

# Build and push each service
build_and_push "frontend-service" "$FRONTEND_REPO" "../../services/frontend-service"
build_and_push "image-service" "$IMAGE_REPO" "../../services/image-service"
build_and_push "auth-service" "$AUTH_REPO" "../../services/auth-service"
build_and_push "colab-service" "$COLAB_REPO" "../../services/colab-service"
build_and_push "annotation-service" "$ANNOTATION_REPO" "../../services/annotation-service"

# Update ECS services to use new images
echo -e "\n${YELLOW}Updating ECS services with new images...${NC}"

# Force new deployment for all services
aws ecs update-service --cluster ${PROJECT_NAME}-cluster --service ${PROJECT_NAME}-front-svc --force-new-deployment --region $AWS_REGION
aws ecs update-service --cluster ${PROJECT_NAME}-cluster --service ${PROJECT_NAME}-back-svc --force-new-deployment --region $AWS_REGION
aws ecs update-service --cluster ${PROJECT_NAME}-cluster --service ${PROJECT_NAME}-auth-svc --force-new-deployment --region $AWS_REGION
aws ecs update-service --cluster ${PROJECT_NAME}-cluster --service ${PROJECT_NAME}-colab-svc --force-new-deployment --region $AWS_REGION
aws ecs update-service --cluster ${PROJECT_NAME}-cluster --service ${PROJECT_NAME}-ann-svc --force-new-deployment --region $AWS_REGION

echo -e "\n${GREEN}🎉 Deployment completed successfully!${NC}"
echo -e "${YELLOW}Application URLs:${NC}"
echo "Frontend: http://$ALB_DNS"
echo "Auth API: http://$ALB_DNS/api/v1/auth"
echo "Images API: http://$ALB_DNS/api/v1/images"
echo "Annotations API: http://$ALB_DNS/api/v1/annotations"
echo "Colab API: http://$ALB_DNS/api/v1/colab"

echo -e "\n${YELLOW}Next steps:${NC}"
echo "1. Configure MongoDB Atlas to allow connections from your AWS VPC IPs"
echo "2. Update your MongoDB connection string in Terraform variables if needed"
echo "3. Monitor service logs in CloudWatch for any connectivity issues"
echo "4. Test the application endpoints"

echo -e "\n${YELLOW}To check service status:${NC}"
echo "aws ecs describe-services --cluster ${PROJECT_NAME}-cluster --services ${PROJECT_NAME}-front-svc ${PROJECT_NAME}-back-svc ${PROJECT_NAME}-auth-svc ${PROJECT_NAME}-colab-svc ${PROJECT_NAME}-ann-svc --region $AWS_REGION"

echo -e "\n${YELLOW}To view logs:${NC}"
echo "aws logs tail /ecs/${PROJECT_NAME} --follow --region $AWS_REGION"