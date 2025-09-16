#!/bin/bash

# BrainLens EKS Deployment Script
# This script sets up the complete EKS infrastructure and deploys the application

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="brainlens"
AWS_REGION="eu-north-1"
CLUSTER_NAME="${PROJECT_NAME}-eks"

echo -e "${BLUE}🚀 BrainLens EKS Deployment Script${NC}"
echo -e "${BLUE}=====================================${NC}"

# Function to check prerequisites
check_prerequisites() {
    echo -e "${YELLOW}🔍 Checking prerequisites...${NC}"

    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        echo -e "${RED}❌ AWS CLI is not installed. Please install it first.${NC}"
        exit 1
    fi

    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        echo -e "${RED}❌ kubectl is not installed. Please install it first.${NC}"
        exit 1
    fi

    # Check Terraform
    if ! command -v terraform &> /dev/null; then
        echo -e "${RED}❌ Terraform is not installed. Please install it first.${NC}"
        exit 1
    fi

    # Check Helm (optional for ingress)
    if ! command -v helm &> /dev/null; then
        echo -e "${YELLOW}⚠️ Helm is not installed. Ingress controller will not be installed automatically.${NC}"
        echo -e "${YELLOW}   You can install it later with: https://helm.sh/docs/intro/install/${NC}"
        SKIP_HELM=true
    else
        SKIP_HELM=false
    fi

    echo -e "${GREEN}✅ All prerequisites are installed${NC}"
}

# Function to setup AWS credentials
setup_aws_credentials() {
    echo -e "${YELLOW}🔐 Setting up AWS credentials...${NC}"

    if [ -z "$AWS_ACCESS_KEY_ID" ] || [ -z "$AWS_SECRET_ACCESS_KEY" ]; then
        echo -e "${RED}❌ AWS credentials not found. Please set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY${NC}"
        exit 1
    fi

    aws configure set aws_access_key_id "$AWS_ACCESS_KEY_ID"
    aws configure set aws_secret_access_key "$AWS_SECRET_ACCESS_KEY"
    aws configure set region "$AWS_REGION"

    echo -e "${GREEN}✅ AWS credentials configured${NC}"
}

# Function to deploy Terraform infrastructure
deploy_terraform() {
    echo -e "${YELLOW}🏗️ Deploying Terraform infrastructure...${NC}"

    cd infra/terraform

    # Initialize Terraform
    terraform init

    # Plan the deployment
    terraform plan -out=tfplan

    # Apply the deployment
    terraform apply tfplan

    # Get outputs
    EKS_CLUSTER_NAME=$(terraform output -raw eks_cluster_name)
    MONGODB_ENDPOINT=$(terraform output -raw mongodb_endpoint)
    MONGODB_PASSWORD=$(terraform output -raw mongodb_password)
    S3_BUCKET_NAME=$(terraform output -raw s3_bucket_name)

    cd ../..

    echo -e "${GREEN}✅ Terraform infrastructure deployed${NC}"
    echo -e "${BLUE}📋 Infrastructure Details:${NC}"
    echo -e "  EKS Cluster: $EKS_CLUSTER_NAME"
    echo -e "  MongoDB Endpoint: $MONGODB_ENDPOINT"
    echo -e "  S3 Bucket: $S3_BUCKET_NAME"
}

# Function to configure kubectl
configure_kubectl() {
    echo -e "${YELLOW}⚙️ Configuring kubectl...${NC}"

    aws eks update-kubeconfig --region "$AWS_REGION" --name "$CLUSTER_NAME"

    # Verify connection
    kubectl cluster-info
    kubectl get nodes

    echo -e "${GREEN}✅ kubectl configured${NC}"
}

# Function to create Kubernetes secrets
create_secrets() {
    echo -e "${YELLOW}🔒 Creating Kubernetes secrets...${NC}"

    # Create namespace
    kubectl apply -f k8s/namespace.yaml

    # Create secrets
    kubectl create secret generic brainlens-secrets \
        --namespace brainlens \
        --from-literal=mongo-username=admin \
        --from-literal=mongo-password="$MONGODB_PASSWORD" \
        --from-literal=aws-access-key-id="$AWS_ACCESS_KEY_ID" \
        --from-literal=aws-secret-access-key="$AWS_SECRET_ACCESS_KEY" \
        --dry-run=client -o yaml | kubectl apply -f -

    echo -e "${GREEN}✅ Kubernetes secrets created${NC}"
}

# Function to deploy MongoDB
deploy_mongodb() {
    echo -e "${YELLOW}🗄️ Deploying MongoDB...${NC}"

    # Update MongoDB deployment with actual endpoint
    sed -i "s|MONGODB_ENDPOINT|$MONGODB_ENDPOINT|g" k8s/mongodb-deployment.yaml

    kubectl apply -f k8s/mongodb-deployment.yaml

    # Wait for MongoDB to be ready
    echo -e "${YELLOW}⏳ Waiting for MongoDB...${NC}"
    kubectl wait --for=condition=ready pod -l app=mongodb -n brainlens --timeout=300s

    echo -e "${GREEN}✅ MongoDB deployed${NC}"
}

# Function to deploy services
deploy_services() {
    echo -e "${YELLOW}🚀 Deploying BrainLens services...${NC}"

    # Update ECR registry in manifests
    ECR_REGISTRY="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
    sed -i "s|{{ECR_REGISTRY}}|$ECR_REGISTRY|g" k8s/*.yaml

    # Deploy services
    kubectl apply -f k8s/configmap.yaml
    kubectl apply -f k8s/auth-service.yaml
    kubectl apply -f k8s/image-service.yaml
    kubectl apply -f k8s/annotation-service.yaml
    kubectl apply -f k8s/colab-service.yaml
    kubectl apply -f k8s/frontend-service.yaml

    # Deploy HPA and network policies
    kubectl apply -f k8s/hpa.yaml
    kubectl apply -f k8s/network-policies.yaml

    echo -e "${GREEN}✅ Services deployed${NC}"
}

# Function to deploy ingress
deploy_ingress() {
    echo -e "${YELLOW}🌐 Deploying ingress...${NC}"

    if [ "$SKIP_HELM" = true ]; then
        echo -e "${YELLOW}⚠️ Skipping NGINX Ingress Controller installation (Helm not available)${NC}"
        echo -e "${YELLOW}   You can install it manually later or use a LoadBalancer service${NC}"

        # Deploy application ingress (may not work without ingress controller)
        kubectl apply -f k8s/ingress.yaml 2>/dev/null || echo -e "${YELLOW}⚠️ Ingress deployment skipped (ingress controller not available)${NC}"
    else
        # Install NGINX Ingress Controller
        helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
        helm repo update

        helm install nginx-ingress ingress-nginx/ingress-nginx \
            --namespace brainlens \
            --set controller.replicaCount=2 \
            --set controller.nodeSelector."kubernetes\.io/os"=linux \
            --set defaultBackend.nodeSelector."kubernetes\.io/os"=linux

        # Deploy application ingress
        kubectl apply -f k8s/ingress.yaml

        echo -e "${GREEN}✅ Ingress deployed${NC}"
    fi
}

# Function to run health checks
run_health_checks() {
    echo -e "${YELLOW}🔍 Running health checks...${NC}"

    # Wait for services to be ready
    sleep 30

    # Check service health
    services=("auth-service:8001" "image-service:8002" "annotation-service:8003" "colab-service:8004")

    for service in "${services[@]}"; do
        name=$(echo "$service" | cut -d: -f1)
        port=$(echo "$service" | cut -d: -f2)

        if kubectl exec -n brainlens "deployment/$name" -- curl -f "http://localhost:$port/health" 2>/dev/null; then
            echo -e "${GREEN}✅ $name is healthy${NC}"
        else
            echo -e "${RED}❌ $name is not responding${NC}"
        fi
    done

    echo -e "${GREEN}✅ Health checks completed${NC}"
}

# Function to show deployment status
show_status() {
    echo -e "${BLUE}📊 Deployment Status${NC}"
    echo -e "${BLUE}==================${NC}"

    echo -e "${YELLOW}Pods:${NC}"
    kubectl get pods -n brainlens

    echo -e "\n${YELLOW}Services:${NC}"
    kubectl get services -n brainlens

    echo -e "\n${YELLOW}Ingress:${NC}"
    kubectl get ingress -n brainlens

    echo -e "\n${GREEN}✅ Deployment completed successfully!${NC}"

    # Get the LoadBalancer URL
    LB_URL=$(kubectl get ingress brainlens-ingress -n brainlens -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null)
    if [ -n "$LB_URL" ]; then
        echo -e "${GREEN}🌍 Access your application at: http://$LB_URL${NC}"
    else
        echo -e "${YELLOW}⏳ Getting LoadBalancer URL...${NC}"
        echo -e "${YELLOW}   Run: kubectl get ingress brainlens-ingress -n brainlens${NC}"
    fi
}

# Main deployment function
main() {
    check_prerequisites
    setup_aws_credentials
    deploy_terraform
    configure_kubectl
    create_secrets
    deploy_mongodb
    deploy_services
    deploy_ingress
    run_health_checks
    show_status

    if [ "$SKIP_HELM" = true ]; then
        echo -e "${YELLOW}📋 Post-deployment steps:${NC}"
        echo -e "${YELLOW}   1. Install Helm: https://helm.sh/docs/intro/install/${NC}"
        echo -e "${YELLOW}   2. Install NGINX Ingress: helm install nginx-ingress ingress-nginx/ingress-nginx${NC}"
        echo -e "${YELLOW}   3. Re-run: kubectl apply -f k8s/ingress.yaml${NC}"
    fi
}

# Run main function
main "$@"