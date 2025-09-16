#!/bin/bash

# Quick script to update Kubernetes MongoDB Atlas secrets
# Run this after deploying to EKS

set -e

echo "🔧 Updating Kubernetes MongoDB Atlas Secrets"
echo "============================================"

# MongoDB Atlas credentials
MONGO_CONNECTION_STRING="mongodb+srv://dbaws:Loannes21@dbtest.hlqdt.mongodb.net/?retryWrites=true&w=majority&appName=DBTest"
MONGO_USERNAME="dbaws"
MONGO_PASSWORD="Loannes21"

# Function to encode to base64
encode_base64() {
    echo -n "$1" | base64
}

# Update secrets
echo "📝 Updating mongo-username..."
kubectl patch secret brainlens-secrets -n brainlens --type merge -p "{
  \"data\": {
    \"mongo-username\": \"$(encode_base64 "$MONGO_USERNAME")\"
  }
}"

echo "📝 Updating mongo-password..."
kubectl patch secret brainlens-secrets -n brainlens --type merge -p "{
  \"data\": {
    \"mongo-password\": \"$(encode_base64 "$MONGO_PASSWORD")\"
  }
}"

echo "📝 Updating mongo-connection-string..."
kubectl patch secret brainlens-secrets -n brainlens --type merge -p "{
  \"data\": {
    \"mongo-connection-string\": \"$(encode_base64 "$MONGO_CONNECTION_STRING")\"
  }
}"

echo ""
echo "✅ MongoDB Atlas secrets updated successfully!"
echo ""
echo "🔍 Verification:"
kubectl get secret brainlens-secrets -n brainlens -o jsonpath='{.data.mongo-username}' | base64 -d && echo " (username)"
kubectl get secret brainlens-secrets -n brainlens -o jsonpath='{.data.mongo-connection-string}' | base64 -d | head -c 50 && echo "... (connection string)"