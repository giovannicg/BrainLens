#!/bin/bash

# MongoDB Atlas Setup Script for BrainLens
# This script helps you configure MongoDB Atlas and update Kubernetes secrets

set -e

echo "🗄️  MongoDB Atlas Setup for BrainLens"
echo "======================================"
echo ""

# Function to encode to base64
encode_base64() {
    echo -n "$1" | base64
}

# Function to update Kubernetes secret
update_k8s_secret() {
    local key=$1
    local value=$2
    local encoded_value=$(encode_base64 "$value")

    echo "Updating Kubernetes secret: $key"
    kubectl patch secret brainlens-secrets -n brainlens --type merge -p "{
      \"data\": {
        \"$key\": \"$encoded_value\"
      }
    }"
}

# Pre-configured MongoDB Atlas credentials
MONGO_CONNECTION_STRING="mongodb+srv://dbaws:Loannes21@dbtest.hlqdt.mongodb.net/?retryWrites=true&w=majority&appName=DBTest"
MONGO_USERNAME="dbaws"
MONGO_PASSWORD="Loannes21"
MONGO_DATABASE="brainlens"

echo "📋 Step 1: MongoDB Atlas Setup Instructions"
echo "--------------------------------------------"
echo "1. Go to https://www.mongodb.com/atlas"
echo "2. Create a free account or sign in"
echo "3. Create a new project called 'BrainLens'"
echo "4. Create a free M0 cluster (Free Tier)"
echo "5. Create a database user with read/write access"
echo "6. Add your IP address to the whitelist (0.0.0.0/0 for development)"
echo "7. Get your connection string from 'Connect' > 'Connect your application'"
echo ""

echo "✅ MongoDB Atlas is pre-configured with your credentials!"
echo ""
echo "📝 Step 2: MongoDB Atlas Details (Pre-configured)"
echo "--------------------------------------------------"
echo "Connection String: $MONGO_CONNECTION_STRING"
echo "Username: $MONGO_USERNAME"
echo "Database: $MONGO_DATABASE"
echo ""

echo ""
echo "🔧 Step 3: Updating Kubernetes Secrets"
echo "---------------------------------------"

# Update Kubernetes secrets
update_k8s_secret "mongo-username" "$MONGO_USERNAME"
update_k8s_secret "mongo-password" "$MONGO_PASSWORD"
update_k8s_secret "mongo-connection-string" "$MONGO_CONNECTION_STRING"

echo ""
echo "✅ Step 4: Verification"
echo "------------------------"

echo "Checking if secrets were updated..."
kubectl get secret brainlens-secrets -n brainlens -o jsonpath='{.data.mongo-username}' | base64 -d
echo " (username)"
kubectl get secret brainlens-secrets -n brainlens -o jsonpath='{.data.mongo-connection-string}' | base64 -d | head -c 50
echo "... (connection string preview)"

echo ""
echo "🎉 Setup Complete!"
echo "=================="
echo ""
echo "Your MongoDB Atlas is now configured for BrainLens!"
echo ""
echo "📋 Next Steps:"
echo "1. Deploy your application: ./infra/terraform/deploy-eks.sh"
echo "2. Check the application logs to ensure MongoDB connection works"
echo "3. Access your application via the LoadBalancer URL"
echo ""
echo "💡 MongoDB Atlas Connection Details:"
echo "   - Database: $MONGO_DATABASE"
echo "   - Username: $MONGO_USERNAME"
echo "   - Connection String: ${MONGO_CONNECTION_STRING:0:50}..."
echo ""
echo "🔒 Your credentials are securely stored in Kubernetes secrets."