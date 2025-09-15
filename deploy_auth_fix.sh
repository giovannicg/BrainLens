#!/bin/bash

# BrainLens Auth Service Deployment Script
# This script builds and deploys the updated auth service with CORS fix

set -e

echo "🚀 Starting BrainLens Auth Service Deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SERVICE_NAME="brainlens-auth-svc"
CLUSTER_NAME="brainlens-cluster"
REGION="eu-north-1"
ECR_REPO_NAME="brainlens-auth"
IMAGE_TAG="cors-fix-$(date +%Y%m%d-%H%M%S)"

echo -e "${BLUE}📋 Configuration:${NC}"
echo "  Service: $SERVICE_NAME"
echo "  Cluster: $CLUSTER_NAME"
echo "  Region: $REGION"
echo "  ECR Repo: $ECR_REPO_NAME"
echo "  Image Tag: $IMAGE_TAG"
echo ""

# Step 1: Build Docker image
echo -e "${YELLOW}🔨 Step 1: Building Docker image...${NC}"
cd services/auth-service
docker build -t $ECR_REPO_NAME:$IMAGE_TAG .
echo -e "${GREEN}✅ Docker image built successfully${NC}"
echo ""

# Step 2: Authenticate with AWS ECR
echo -e "${YELLOW}🔐 Step 2: Authenticating with AWS ECR...${NC}"
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $(aws sts get-caller-identity --query Account --output text).dkr.ecr.$REGION.amazonaws.com
echo -e "${GREEN}✅ Authenticated with ECR${NC}"
echo ""

# Step 3: Tag and push image
echo -e "${YELLOW}📤 Step 3: Pushing image to ECR...${NC}"
ECR_URI=$(aws ecr describe-repositories --repository-names $ECR_REPO_NAME --region $REGION --query 'repositories[0].repositoryUri' --output text)
docker tag $ECR_REPO_NAME:$IMAGE_TAG $ECR_URI:$IMAGE_TAG
docker push $ECR_URI:$IMAGE_TAG
echo -e "${GREEN}✅ Image pushed to ECR: $ECR_URI:$IMAGE_TAG${NC}"
echo ""

# Step 4: Update ECS service
echo -e "${YELLOW}🔄 Step 4: Updating ECS service...${NC}"
TASK_DEFINITION_ARN=$(aws ecs describe-services --cluster $CLUSTER_NAME --services $SERVICE_NAME --region $REGION --query 'services[0].taskDefinition' --output text)
TASK_DEFINITION_FAMILY=$(echo $TASK_DEFINITION_ARN | cut -d'/' -f2 | cut -d':' -f1)

echo "Current task definition: $TASK_DEFINITION_ARN"
echo "Task definition family: $TASK_DEFINITION_FAMILY"

# Get current task definition
aws ecs describe-task-definition --task-definition $TASK_DEFINITION_FAMILY --region $REGION > current_task_def.json

# Update the image URI in the task definition
sed -i "s|\"image\": \"[^\"]*\"|\"image\": \"$ECR_URI:$IMAGE_TAG\"|g" current_task_def.json

# Remove fields that can't be in register-task-definition
jq 'del(.taskDefinitionArn, .revision, .status, .requiresAttributes, .compatibilities, .registeredAt, .registeredBy)' current_task_def.json > updated_task_def.json

# Register new task definition
NEW_TASK_DEF_ARN=$(aws ecs register-task-definition --cli-input-json file://updated_task_def.json --region $REGION --query 'taskDefinition.taskDefinitionArn' --output text)

echo "New task definition: $NEW_TASK_DEF_ARN"

# Update service with new task definition
aws ecs update-service --cluster $CLUSTER_NAME --service $SERVICE_NAME --task-definition $NEW_TASK_DEF_ARN --region $REGION --force-new-deployment

echo -e "${GREEN}✅ ECS service updated successfully${NC}"
echo ""

# Step 5: Wait for deployment
echo -e "${YELLOW}⏳ Step 5: Waiting for deployment to complete...${NC}"
echo "This may take a few minutes..."

# Wait for service to be stable
aws ecs wait services-stable --cluster $CLUSTER_NAME --services $SERVICE_NAME --region $REGION

echo -e "${GREEN}✅ Deployment completed successfully!${NC}"
echo ""

# Step 6: Verify deployment
echo -e "${BLUE}🔍 Step 6: Verifying deployment...${NC}"
SERVICE_STATUS=$(aws ecs describe-services --cluster $CLUSTER_NAME --services $SERVICE_NAME --region $REGION --query 'services[0].runningCount' --output text)
echo "Running tasks: $SERVICE_STATUS"

if [ "$SERVICE_STATUS" -gt 0 ]; then
    echo -e "${GREEN}🎉 Auth service is running successfully!${NC}"
    echo ""
    echo -e "${BLUE}🌐 Test the CORS fix:${NC}"
    echo "Frontend URL: http://brainlens-alb-344103177.eu-north-1.elb.amazonaws.com"
    echo "Try registering a user - the CORS error should be fixed!"
else
    echo -e "${RED}❌ Service deployment failed${NC}"
    exit 1
fi

# Cleanup
rm -f current_task_def.json updated_task_def.json

echo ""
echo -e "${GREEN}🎊 BrainLens Auth Service deployment completed!${NC}"