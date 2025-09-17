#!/bin/bash

# Setup GitHub Repository Variables for BrainLens CI/CD
# This script helps you configure GitHub repository variables

set -e

echo "🚀 GitHub Repository Variables Setup for BrainLens"
echo "=================================================="
echo ""

# ECR Repository URIs
ECR_FRONTEND_URI="328764941686.dkr.ecr.eu-north-1.amazonaws.com/brainlens-frontend"
ECR_AUTH_URI="328764941686.dkr.ecr.eu-north-1.amazonaws.com/brainlens-auth"
ECR_IMAGE_URI="328764941686.dkr.ecr.eu-north-1.amazonaws.com/brainlens-image"
ECR_ANNOTATION_URI="328764941686.dkr.ecr.eu-north-1.amazonaws.com/brainlens-annotation"
ECR_COLAB_URI="328764941686.dkr.ecr.eu-north-1.amazonaws.com/brainlens-colab"

# EKS Information
EKS_CLUSTER_NAME="brainlens-eks"
EKS_CLUSTER_ENDPOINT="https://7E498AE1A0F2D9DC61E53E8E1FD04088.gr7.eu-north-1.eks.amazonaws.com"

# S3 Bucket
S3_BUCKET_NAME="brainlens-storage-v8q35chb"

# AWS Region
AWS_REGION="eu-north-1"

echo "📋 Required GitHub Repository Variables:"
echo "=========================================="
echo ""
echo "🔑 AWS Credentials (Required):"
echo "  AWS_ACCESS_KEY_ID     → Your AWS access key"
echo "  AWS_SECRET_ACCESS_KEY → Your AWS secret key"
echo "  AWS_ACCOUNT_ID        → 328764941686"
echo "  AWS_REGION           → $AWS_REGION"
echo ""

echo "🏗️  Infrastructure Variables:"
echo "  EKS_CLUSTER_NAME     → $EKS_CLUSTER_NAME"
echo "  EKS_CLUSTER_ENDPOINT → $EKS_CLUSTER_ENDPOINT"
echo "  S3_BUCKET_NAME       → $S3_BUCKET_NAME"
echo ""

echo "🐳 ECR Repository URIs:"
echo "  ECR_FRONTEND_URI     → $ECR_FRONTEND_URI"
echo "  ECR_AUTH_URI         → $ECR_AUTH_URI"
echo "  ECR_IMAGE_URI        → $ECR_IMAGE_URI"
echo "  ECR_ANNOTATION_URI   → $ECR_ANNOTATION_URI"
echo "  ECR_COLAB_URI        → $ECR_COLAB_URI"
echo ""

echo "📝 Setup Instructions:"
echo "======================"
echo ""
echo "1. Go to your GitHub repository"
echo "2. Navigate to: Settings → Secrets and variables → Actions"
echo "3. Click 'Variables' tab"
echo "4. Add each variable using the 'New repository variable' button"
echo ""

echo "🔧 Copy these values to add to GitHub:"
echo "======================================"
echo ""
echo "# AWS Credentials"
echo "AWS_ACCESS_KEY_ID=your_aws_access_key_here"
echo "AWS_SECRET_ACCESS_KEY=your_aws_secret_key_here"
echo "AWS_ACCOUNT_ID=328764941686"
echo "AWS_REGION=$AWS_REGION"
echo ""
echo "# EKS Information"
echo "EKS_CLUSTER_NAME=$EKS_CLUSTER_NAME"
echo "EKS_CLUSTER_ENDPOINT=$EKS_CLUSTER_ENDPOINT"
echo ""
echo "# S3 Bucket"
echo "S3_BUCKET_NAME=$S3_BUCKET_NAME"
echo ""
echo "# ECR Repository URIs"
echo "ECR_FRONTEND_URI=$ECR_FRONTEND_URI"
echo "ECR_AUTH_URI=$ECR_AUTH_URI"
echo "ECR_IMAGE_URI=$ECR_IMAGE_URI"
echo "ECR_ANNOTATION_URI=$ECR_ANNOTATION_URI"
echo "ECR_COLAB_URI=$ECR_COLAB_URI"
echo ""

echo "✅ After adding all variables:"
echo "=============================="
echo ""
echo "1. Your GitHub Actions workflows will automatically use these values"
echo "2. CI/CD pipelines will build and push to the correct ECR repositories"
echo "3. Deployments will target the correct EKS cluster"
echo "4. S3 bucket will be used for file storage"
echo ""

echo "🎯 Next Steps:"
echo "=============="
echo ""
echo "1. Add all variables to GitHub repository"
echo "2. Push your code to trigger CI/CD"
echo "3. Monitor the GitHub Actions for successful builds"
echo "4. Deploy using: ./infra/terraform/deploy-eks.sh"
echo ""

echo "💡 Pro Tips:"
echo "============"
echo ""
echo "• Keep AWS credentials secure - never commit them to code"
echo "• Use GitHub repository variables for environment-specific values"
echo "• Test your CI/CD pipeline after setup"
echo "• Monitor costs in AWS Console"
echo ""

echo "🚀 Ready for automated deployments!"