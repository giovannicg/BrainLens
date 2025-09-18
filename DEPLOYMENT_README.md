# 🚀 BrainLens - Complete Deployment Guide

## 📋 Overview

BrainLens is a complete medical imaging platform with AI-powered tumor detection, built for AWS EKS with MongoDB Atlas.

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   MongoDB       │
│   (React)       │◄──►│   Atlas         │
│   Port: 3000    │    │   (Cloud)       │
└─────────────────┘    └─────────────────┘
         │
    ┌────▼────┐
    │  Auth   │
    │ Service │
    │ Port: 8001 │
    └────▲────┘
         │
    ┌────▼────┐    ┌─────────────────┐
    │  Image  │    │   Colab Service │
    │ Service │    │   Port: 8004    │
    │ Port: 8002 │    │   (ngrok)     │
    └────▲────┘    └─────────────────┘
         │
    ┌────▼────┐
    │Annotation│
    │ Service │
    │ Port: 8003 │
    └──────────┘
```

## 🎯 Quick Start

### 1. Setup GitHub Repository Variables

Copy these variables to: **GitHub → Settings → Secrets and variables → Actions → Variables**

```bash
# AWS Credentials
AWS_ACCESS_KEY_ID=your_aws_access_key_here
AWS_SECRET_ACCESS_KEY=your_aws_secret_key_here
AWS_ACCOUNT_ID=328764941686
AWS_REGION=eu-north-1

# EKS Information
EKS_CLUSTER_NAME=brainlens-eks
EKS_CLUSTER_ENDPOINT=https://7E498AE1A0F2D9DC61E53E8E1FD04088.gr7.eu-north-1.eks.amazonaws.com

# S3 Bucket
S3_BUCKET_NAME=brainlens-storage-v8q35chb

# ECR Repository URIs
ECR_FRONTEND_URI=328764941686.dkr.ecr.eu-north-1.amazonaws.com/brainlens-frontend
ECR_AUTH_URI=328764941686.dkr.ecr.eu-north-1.amazonaws.com/brainlens-auth
ECR_IMAGE_URI=328764941686.dkr.ecr.eu-north-1.amazonaws.com/brainlens-image
ECR_ANNOTATION_URI=328764941686.dkr.ecr.eu-north-1.amazonaws.com/brainlens-annotation
ECR_COLAB_URI=328764941686.dkr.ecr.eu-north-1.amazonaws.com/brainlens-colab

# MongoDB Atlas
MONGODB_CONNECTION_STRING=mongodb+srv://dbaws:Loannes21@dbtest.hlqdt.mongodb.net/?retryWrites=true&w=majority&appName=DBTest
MONGODB_USERNAME=dbaws
MONGODB_PASSWORD=Loannes21
```

### 2. Deploy Infrastructure

```bash
cd infra/terraform
terraform init
terraform apply
```

### 3. Setup MongoDB Atlas Secrets

```bash
./update_k8s_mongo_secrets.sh
```

### 4. Push Code to Trigger CI/CD

```bash
git add .
git commit -m "Deploy BrainLens to production"
git push origin main
```

## 🔄 CI/CD Pipeline

### Build Pipeline (`.github/workflows/ci-cd.yml`)
- **Triggers:** Push to `main` or `develop` branches
- **Builds:** All 5 microservices (Auth, Image, Annotation, Colab, Frontend)
- **Pushes:** Docker images to Amazon ECR
- **Duration:** ~10-15 minutes

### Deploy Pipeline (`.github/workflows/eks-deploy.yml`)
- **Triggers:** When build pipeline completes successfully
- **Deploys:** All services to EKS cluster
- **Health Checks:** Verifies all services are running
- **Duration:** ~5-10 minutes

## 📊 Monitoring & Debugging

### Check Pipeline Status
```bash
# GitHub: Repository → Actions tab
```

### Check EKS Deployment
```bash
kubectl get pods -n brainlens
kubectl get services -n brainlens
kubectl get ingress -n brainlens
```

### Check Application Logs
```bash
kubectl logs -n brainlens deployment/frontend-service
kubectl logs -n brainlens deployment/auth-service
kubectl logs -n brainlens deployment/image-service
```

### Get Application URL
```bash
kubectl get ingress brainlens-ingress -n brainlens
```

## 🔧 Manual Deployment (Alternative)

If you prefer manual deployment:

```bash
# 1. Build and push images
cd infra/terraform
./deploy-eks.sh

# 2. Deploy to Kubernetes
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/auth-service.yaml
kubectl apply -f k8s/image-service.yaml
kubectl apply -f k8s/annotation-service.yaml
kubectl apply -f k8s/colab-service.yaml
kubectl apply -f k8s/frontend-service.yaml
kubectl apply -f k8s/ingress.yaml
```

## 🗄️ MongoDB Atlas Setup

### Pre-configured Connection
- **Connection String:** `mongodb+srv://dbaws:Loannes21@dbtest.hlqdt.mongodb.net`
- **Username:** `dbaws`
- **Password:** `Loannes21`
- **Database:** `brainlens`

### Update Connection (if needed)
```bash
./setup_mongodb_atlas.sh
```

## 🧠 Colab Integration

### Current Configuration
- **Predict URL:** `https://877a172a4c64.ngrok-free.app/predict`
- **Raw URL:** `https://877a172a4c64.ngrok-free.app/predict-raw`

### Update Colab URLs
```bash
./update_colab_urls.sh "https://your-new-ngrok-url.ngrok-free.app"
```

## 📁 Project Structure

```
brainlens/
├── services/                 # Microservices
│   ├── auth-service/        # Authentication
│   ├── image-service/       # Image processing
│   ├── annotation-service/  # Medical annotations
│   ├── colab-service/       # AI predictions
│   └── frontend-service/    # React application
├── infra/terraform/         # Infrastructure as Code
├── k8s/                     # Kubernetes manifests
├── .github/workflows/       # CI/CD pipelines
└── scripts/                 # Deployment scripts
```

## 🚨 Troubleshooting

### Common Issues

#### 1. Pipeline Fails
```bash
# Check GitHub Actions logs
# Verify all repository variables are set
# Check AWS credentials have correct permissions
```

#### 2. EKS Deployment Fails
```bash
kubectl get pods -n brainlens
kubectl describe pod <pod-name> -n brainlens
kubectl logs <pod-name> -n brainlens
```

#### 3. Services Not Healthy
```bash
kubectl exec -n brainlens deployment/auth-service -- curl http://localhost:8001/health
kubectl exec -n brainlens deployment/image-service -- curl http://localhost:8002/health
```

#### 4. MongoDB Connection Issues
```bash
kubectl get secret brainlens-secrets -n brainlens -o jsonpath='{.data.mongo-connection-string}' | base64 -d
./update_k8s_mongo_secrets.sh
```

## 📞 Support

- **Documentation:** Check this README and inline comments
- **Logs:** Use `kubectl logs` and GitHub Actions
- **Health Checks:** All services have `/health` endpoints
- **Monitoring:** Use `kubectl get` commands for status

## 🎉 Success!

Once deployed, your BrainLens application will be available at:
```
http://<load-balancer-url>
```

**Happy deploying! 🚀**