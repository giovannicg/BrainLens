#!/bin/bash

# Script to update Colab URLs in Kubernetes ConfigMap
# Usage: ./update_colab_urls.sh "https://your-new-ngrok-url.ngrok-free.app"

set -e

if [ $# -ne 1 ]; then
    echo "Usage: $0 <ngrok-url>"
    echo "Example: $0 https://abc123.ngrok-free.app"
    exit 1
fi

NGROK_URL=$1

# Remove trailing slash if present
NGROK_URL=${NGROK_URL%/}

echo "Updating Colab URLs to: $NGROK_URL"

# Update the ConfigMap
kubectl patch configmap brainlens-config -n brainlens --type merge -p "{
  \"data\": {
    \"COLAB_PREDICT_URL\": \"$NGROK_URL/predict\",
    \"COLAB_PREDICT_RAW_URL\": \"$NGROK_URL/predict-raw\"
  }
}"

echo "✅ Colab URLs updated successfully!"
echo "📋 New URLs:"
echo "   Predict: $NGROK_URL/predict"
echo "   Raw:     $NGROK_URL/predict-raw"
echo ""
echo "🔄 The changes will take effect automatically (no restart needed)"
echo "   Pods will pick up the new URLs within 1-2 minutes"