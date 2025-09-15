# BrainLens AWS Production Deployment

This directory contains the Terraform configuration for deploying BrainLens to AWS ECS Fargate.

## Prerequisites

- AWS CLI configured with appropriate permissions
- Terraform >= 1.5.0
- Docker
- MongoDB Atlas account

## Quick Start

1. **Configure MongoDB Atlas Network Access**
   ```bash
   # In MongoDB Atlas dashboard:
   # Go to Network Access → Add IP Address
   # Add your AWS VPC public IP ranges or 0.0.0.0/0 for testing
   ```

2. **Update Terraform Variables**
   ```bash
   # Create terraform.tfvars file or set environment variables
   export TF_VAR_mongo_url="mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority"
   export TF_VAR_bedrock_model_id="amazon.nova-lite-v1:0"
   ```

3. **Deploy Infrastructure**
   ```bash
   cd infra/terraform
   terraform init
   terraform plan
   terraform apply
   ```

4. **Build and Push Docker Images**
   ```bash
   # Authenticate with ECR
   aws ecr get-login-password --region eu-north-1 | docker login --username AWS --password-stdin ACCOUNT_ID.dkr.ecr.eu-north-1.amazonaws.com

   # Build and push images (replace ACCOUNT_ID)
   docker build -t frontend ../../services/frontend-service
   docker tag frontend:latest ACCOUNT_ID.dkr.ecr.eu-north-1.amazonaws.com/brainlens-frontend:latest
   docker push ACCOUNT_ID.dkr.ecr.eu-north-1.amazonaws.com/brainlens-frontend:latest

   # Repeat for other services: image-service, auth-service, colab-service, annotation-service
   ```

5. **Update ECS Services**
   ```bash
   # Force deployment to use new images
   aws ecs update-service --cluster brainlens-cluster --service brainlens-front-svc --force-new-deployment
   aws ecs update-service --cluster brainlens-cluster --service brainlens-back-svc --force-new-deployment
   aws ecs update-service --cluster brainlens-cluster --service brainlens-auth-svc --force-new-deployment
   aws ecs update-service --cluster brainlens-cluster --service brainlens-colab-svc --force-new-deployment
   aws ecs update-service --cluster brainlens-cluster --service brainlens-ann-svc --force-new-deployment
   ```

## Architecture

### Networking
- **VPC**: 10.0.0.0/16 with public subnets in eu-north-1a and eu-north-1b
- **ALB**: Application Load Balancer with path-based routing
- **Security Groups**: Properly configured for ALB-to-ECS communication
- **VPC Endpoints**: S3 gateway endpoint for optimized connectivity

### Services
- **Frontend**: React app served on port 3000
- **Image Service**: Main backend API on port 8002
- **Auth Service**: Authentication API on port 8001
- **Annotation Service**: Annotations API on port 8003
- **Colab Service**: ML prediction service on port 8004

### Routing
- `/` → Frontend (port 3000)
- `/api/*` → Image Service (port 8002)
- `/api/v1/auth/*` → Auth Service (port 8001)
- `/api/v1/annotations/*` → Annotation Service (port 8003)
- `/api/v1/colab/*` → Colab Service (port 8004)

## Health Checks

All services have health check endpoints:
- Frontend: `/`
- Image Service: `/api/v1/images/health`
- Auth Service: `/api/v1/auth/health`
- Annotation Service: `/api/v1/annotations/health`
- Colab Service: `/health`

## Environment Variables

### Required Variables
- `mongo_url`: MongoDB Atlas connection string
- `bedrock_model_id`: AWS Bedrock model ID (default: amazon.nova-lite-v1:0)
- `aws_region`: AWS region (default: eu-north-1)
- `vlm_timeout`: VLM request timeout in seconds (default: 300)

### Service-Specific Variables
Each service receives:
- `MONGODB_URL`: Database connection
- `DATABASE_NAME`: Database name (brainlens)
- `ENVIRONMENT`: Set to "production"
- `ALB_DNS_NAME`: Load balancer DNS for CORS
- `DEBUG`: Set to "false"

## Monitoring

### CloudWatch Logs
All services log to `/ecs/brainlens` log group with service-specific prefixes.

### Service Status
```bash
aws ecs describe-services --cluster brainlens-cluster --services brainlens-front-svc brainlens-back-svc --region eu-north-1
```

### Logs
```bash
aws logs tail /ecs/brainlens --follow --region eu-north-1
```

## Troubleshooting

### Common Issues

1. **MongoDB Connection Failed**
   - Check MongoDB Atlas network access settings
   - Verify connection string in Terraform variables
   - Ensure VPC security groups allow outbound connections

2. **Health Checks Failing**
   - Verify health check paths match service endpoints
   - Check service logs for startup errors
   - Ensure services can connect to MongoDB

3. **Service Communication Issues**
   - Verify ALB DNS is correctly set in environment variables
   - Check security groups allow traffic between services
   - Ensure services are running and healthy

4. **Image Pull Errors**
   - Verify ECR repository permissions
   - Check Docker image tags match Terraform configuration
   - Ensure AWS credentials have ECR access

### Debugging Commands

```bash
# Check service events
aws ecs describe-services --cluster brainlens-cluster --services brainlens-back-svc --region eu-north-1 --query 'services[0].events[0:5]'

# Check task status
aws ecs list-tasks --cluster brainlens-cluster --region eu-north-1

# Get task details
aws ecs describe-tasks --cluster brainlens-cluster --tasks TASK_ID --region eu-north-1

# View container logs
aws logs get-log-events --log-group-name /ecs/brainlens --log-stream-name image/TASK_ID --region eu-north-1
```

## Security Considerations

- ALB only accepts HTTP traffic (consider adding HTTPS listener)
- ECS tasks run in private subnets with public IPs
- Security groups restrict traffic to necessary ports only
- IAM roles provide minimal required permissions
- MongoDB Atlas should restrict IP access to VPC ranges

## Cost Optimization

- Use Fargate Spot for non-critical workloads
- Configure auto-scaling based on CPU/memory usage
- Set appropriate task sizes (CPU/memory allocation)
- Use VPC endpoints to reduce data transfer costs
- Configure CloudWatch log retention appropriately