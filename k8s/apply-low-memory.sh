#!/bin/bash

echo "🚀 Aplicando deployments con límites de memoria reducidos..."

# Aplicar todos los deployments
kubectl apply -f namespace.yaml
kubectl apply -f configmap.yaml
kubectl apply -f secret.yaml

echo "📦 Aplicando servicios..."
kubectl apply -f image-service.yaml
kubectl apply -f auth-service.yaml
kubectl apply -f colab-service.yaml
kubectl apply -f annotation-service.yaml
kubectl apply -f frontend-service.yaml

echo "📊 Aplicando HPA..."
kubectl apply -f hpa.yaml

echo "⏳ Esperando que los pods estén listos..."
kubectl wait --for=condition=ready pod -l app=image-service -n brainlens --timeout=300s
kubectl wait --for=condition=ready pod -l app=auth-service -n brainlens --timeout=300s
kubectl wait --for=condition=ready pod -l app=colab-service -n brainlens --timeout=300s
kubectl wait --for=condition=ready pod -l app=annotation-service -n brainlens --timeout=300s
kubectl wait --for=condition=ready pod -l app=frontend-service -n brainlens --timeout=300s

echo "📋 Estado de los pods:"
kubectl get pods -n brainlens

echo "💾 Uso de recursos por nodo:"
kubectl top nodes

echo "📊 Uso de recursos por pod:"
kubectl top pods -n brainlens

echo "✅ Deployment completado!"
