# BrainLens AKS Deployment Guide

## Overview

This guide provides a comprehensive plan for deploying BrainLens to Azure Kubernetes Service (AKS) with localhost-style service communication.

## Architecture Overview

### Current Docker Compose Architecture
- **Frontend Service**: React app on port 3000
- **Auth Service**: Python FastAPI on port 8001
- **Image Service**: Python FastAPI on port 8002
- **Annotation Service**: Python FastAPI on port 8003
- **Colab Service**: Python FastAPI on port 8004
- **MongoDB**: Database on port 27017
- **Ollama**: AI model service on port 11434

### Target AKS Architecture
```
Internet → Azure Load Balancer → NGINX Ingress → Services
                                       ↓
MongoDB (Azure Database) ← Services (localhost communication)
```

## Prerequisites

- Azure CLI installed and configured
- kubectl installed
- Helm 3.x installed
- Azure subscription with AKS permissions

## 1. AKS Cluster Setup

### Create Resource Group
```bash
az group create --name brainlens-rg --location westeurope
```

### Create AKS Cluster
```bash
az aks create \
  --resource-group brainlens-rg \
  --name brainlens-aks \
  --node-count 3 \
  --enable-managed-identity \
  --generate-ssh-keys \
  --network-plugin azure \
  --service-cidr 10.0.0.0/16 \
  --dns-service-ip 10.0.0.10 \
  --docker-bridge-address 172.17.0.1/16
```

### Configure kubectl
```bash
az aks get-credentials --resource-group brainlens-rg --name brainlens-aks
```

## 2. MongoDB Setup

### Option A: Azure Cosmos DB (Recommended)
```bash
az cosmosdb create \
  --name brainlens-mongo \
  --resource-group brainlens-rg \
  --kind MongoDB \
  --server-version 4.0 \
  --default-consistency-level Session \
  --enable-automatic-failover true
```

### Option B: MongoDB in Kubernetes
```yaml
# k8s/mongodb-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mongodb
spec:
  replicas: 1
  selector:
    matchLabels:
      app: mongodb
  template:
    metadata:
      labels:
        app: mongodb
    spec:
      containers:
      - name: mongodb
        image: mongo:7.0
        ports:
        - containerPort: 27017
        env:
        - name: MONGO_INITDB_ROOT_USERNAME
          value: "admin"
        - name: MONGO_INITDB_ROOT_PASSWORD
          value: "password"
        - name: MONGO_INITDB_DATABASE
          value: "brainlens"
        volumeMounts:
        - name: mongodb-storage
          mountPath: /data/db
      volumes:
      - name: mongodb-storage
        persistentVolumeClaim:
          claimName: mongodb-pvc

---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: mongodb-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 50Gi
```

## 3. Kubernetes Manifests

### Namespace
```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: brainlens
  labels:
    name: brainlens
```

### ConfigMaps and Secrets

```yaml
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: brainlens-config
  namespace: brainlens
data:
  ENVIRONMENT: "production"
  DATABASE_NAME: "brainlens"
  VLM_PROVIDER: "bedrock"
  BEDROCK_MODEL_ID: "amazon.nova-lite-v1:0"
  AWS_REGION: "eu-north-1"
  VLM_TIMEOUT: "300"
  DEBUG: "false"

---
# k8s/secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: brainlens-secrets
  namespace: brainlens
type: Opaque
data:
  # Base64 encoded values
  MONGO_USERNAME: YWRtaW4=  # admin
  MONGO_PASSWORD: cGFzc3dvcmQ=  # password
  AWS_ACCESS_KEY_ID: <base64-encoded>
  AWS_SECRET_ACCESS_KEY: <base64-encoded>
  COLAB_PREDICT_URL: <base64-encoded>
```

### Service Deployments

```yaml
# k8s/auth-service.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: auth-service
  namespace: brainlens
spec:
  replicas: 2
  selector:
    matchLabels:
      app: auth-service
  template:
    metadata:
      labels:
        app: auth-service
    spec:
      containers:
      - name: auth-service
        image: brainlens/auth-service:latest
        ports:
        - containerPort: 8001
        env:
        - name: MONGODB_URL
          value: "mongodb://$(MONGO_USERNAME):$(MONGO_PASSWORD)@mongodb.brainlens.svc.cluster.local:27017"
        - name: HOST
          value: "0.0.0.0"
        - name: PORT
          value: "8001"
        envFrom:
        - configMapRef:
            name: brainlens-config
        - secretRef:
            name: brainlens-secrets
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /api/v1/auth/health
            port: 8001
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /api/v1/auth/health
            port: 8001
          initialDelaySeconds: 5
          periodSeconds: 5

---
apiVersion: v1
kind: Service
metadata:
  name: auth-service
  namespace: brainlens
spec:
  selector:
    app: auth-service
  ports:
  - port: 8001
    targetPort: 8001
  type: ClusterIP
```

```yaml
# k8s/image-service.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: image-service
  namespace: brainlens
spec:
  replicas: 2
  selector:
    matchLabels:
      app: image-service
  template:
    metadata:
      labels:
        app: image-service
    spec:
      containers:
      - name: image-service
        image: brainlens/image-service:latest
        ports:
        - containerPort: 8002
        env:
        - name: MONGODB_URL
          value: "mongodb://$(MONGO_USERNAME):$(MONGO_PASSWORD)@mongodb.brainlens.svc.cluster.local:27017"
        - name: COLAB_SERVICE_URL
          value: "http://colab-service.brainlens.svc.cluster.local:8004"
        - name: HOST
          value: "0.0.0.0"
        - name: PORT
          value: "8002"
        envFrom:
        - configMapRef:
            name: brainlens-config
        - secretRef:
            name: brainlens-secrets
        volumeMounts:
        - name: image-storage
          mountPath: /app/storage
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /api/v1/images/health
            port: 8002
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /api/v1/images/health
            port: 8002
          initialDelaySeconds: 5
          periodSeconds: 5
      volumes:
      - name: image-storage
        persistentVolumeClaim:
          claimName: image-storage-pvc

---
apiVersion: v1
kind: Service
metadata:
  name: image-service
  namespace: brainlens
spec:
  selector:
    app: image-service
  ports:
  - port: 8002
    targetPort: 8002
  type: ClusterIP
```

### Persistent Storage

```yaml
# k8s/storage.yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: image-storage-pvc
  namespace: brainlens
spec:
  accessModes:
    - ReadWriteMany
  resources:
    requests:
      storage: 100Gi
  storageClassName: azurefile-premium

---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: ollama-storage-pvc
  namespace: brainlens
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 50Gi
  storageClassName: default
```

## 4. Ingress Configuration

### Install NGINX Ingress Controller
```bash
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update
helm install nginx-ingress ingress-nginx/ingress-nginx \
  --namespace brainlens \
  --set controller.replicaCount=2 \
  --set controller.nodeSelector."kubernetes\.io/os"=linux \
  --set defaultBackend.nodeSelector."kubernetes\.io/os"=linux
```

### Ingress Resource
```yaml
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: brainlens-ingress
  namespace: brainlens
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - brainlens.yourdomain.com
    secretName: brainlens-tls
  rules:
  - host: brainlens.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: frontend-service
            port:
              number: 3000
      - path: /api/v1/auth
        pathType: Prefix
        backend:
          service:
            name: auth-service
            port:
              number: 8001
      - path: /api/v1/images
        pathType: Prefix
        backend:
          service:
            name: image-service
            port:
              number: 8002
      - path: /api/v1/annotations
        pathType: Prefix
        backend:
          service:
            name: annotation-service
            port:
              number: 8003
      - path: /api/v1/colab
        pathType: Prefix
        backend:
          service:
            name: colab-service
            port:
              number: 8004
```

## 5. Service Communication

### Internal Service URLs
With Kubernetes DNS, services communicate using:
- `auth-service.brainlens.svc.cluster.local:8001`
- `image-service.brainlens.svc.cluster.local:8002`
- `annotation-service.brainlens.svc.cluster.local:8003`
- `colab-service.brainlens.svc.cluster.local:8004`
- `mongodb.brainlens.svc.cluster.local:27017`

### Frontend Environment Variables
```yaml
# In frontend deployment
env:
- name: REACT_APP_API_BASE_URL
  value: "https://brainlens.yourdomain.com/api/v1"
```

## 6. Monitoring and Logging

### Install Prometheus and Grafana
```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace
```

### Azure Monitor Integration
```bash
az monitor diagnostic-settings create \
  --name brainlens-diagnostics \
  --resource /subscriptions/.../resourceGroups/brainlens-rg/providers/Microsoft.ContainerService/managedClusters/brainlens-aks \
  --logs '["kube-apiserver","kube-controller-manager","kube-scheduler","kube-audit"]' \
  --metrics '["AllMetrics"]' \
  --workspace /subscriptions/.../resourceGroups/.../providers/Microsoft.OperationalInsights/workspaces/brainlens-logs
```

## 7. CI/CD Pipeline

### Azure DevOps Pipeline
```yaml
# azure-pipelines.yml
trigger:
  branches:
    include:
    - main

stages:
- stage: Build
  jobs:
  - job: BuildAndPush
    steps:
    - task: Docker@2
      inputs:
        command: 'buildAndPush'
        repository: 'brainlens/$(serviceName)'
        dockerfile: 'services/$(serviceName)/Dockerfile'
        containerRegistry: 'brainlens-acr'
        tags: |
          $(Build.BuildId)
          latest

- stage: Deploy
  jobs:
  - deployment: DeployToAKS
    environment: 'production'
    strategy:
      runOnce:
        deploy:
          steps:
          - task: KubernetesManifest@0
            inputs:
              action: 'deploy'
              namespace: 'brainlens'
              manifests: 'k8s/$(serviceName).yaml'
```

## 8. Deployment Scripts

### Deploy Script
```bash
#!/bin/bash
# deploy.sh

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting BrainLens AKS Deployment${NC}"

# Check prerequisites
command -v az >/dev/null 2>&1 || { echo -e "${RED}❌ Azure CLI is required${NC}"; exit 1; }
command -v kubectl >/dev/null 2>&1 || { echo -e "${RED}❌ kubectl is required${NC}"; exit 1; }

# Create namespace
echo -e "${YELLOW}📦 Creating namespace...${NC}"
kubectl apply -f k8s/namespace.yaml

# Deploy MongoDB
echo -e "${YELLOW}🗄️ Deploying MongoDB...${NC}"
kubectl apply -f k8s/mongodb-deployment.yaml

# Wait for MongoDB
echo -e "${YELLOW}⏳ Waiting for MongoDB...${NC}"
kubectl wait --for=condition=ready pod -l app=mongodb -n brainlens --timeout=300s

# Deploy services
echo -e "${YELLOW}🔧 Deploying services...${NC}"
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/auth-service.yaml
kubectl apply -f k8s/image-service.yaml
kubectl apply -f k8s/annotation-service.yaml
kubectl apply -f k8s/colab-service.yaml
kubectl apply -f k8s/frontend-service.yaml

# Deploy ingress
echo -e "${YELLOW}🌐 Deploying ingress...${NC}"
kubectl apply -f k8s/ingress.yaml

# Wait for deployments
echo -e "${YELLOW}⏳ Waiting for deployments...${NC}"
kubectl wait --for=condition=available --timeout=600s deployment/auth-service -n brainlens
kubectl wait --for=condition=available --timeout=600s deployment/image-service -n brainlens
kubectl wait --for=condition=available --timeout=600s deployment/annotation-service -n brainlens
kubectl wait --for=condition=available --timeout=600s deployment/colab-service -n brainlens
kubectl wait --for=condition=available --timeout=600s deployment/frontend-service -n brainlens

echo -e "${GREEN}✅ BrainLens deployment completed successfully!${NC}"
echo -e "${GREEN}🌍 Access your application at: https://brainlens.yourdomain.com${NC}"
```

### Health Check Script
```bash
#!/bin/bash
# health-check.sh

echo "🔍 Checking BrainLens services health..."

# Check all services
services=("auth-service:8001" "image-service:8002" "annotation-service:8003" "colab-service:8004" "frontend-service:3000")

for service in "${services[@]}"; do
  name=$(echo $service | cut -d: -f1)
  port=$(echo $service | cut -d: -f2)

  if kubectl exec -n brainlens deployment/$name -- curl -f http://localhost:$port/health 2>/dev/null; then
    echo "✅ $name is healthy"
  else
    echo "❌ $name is not responding"
  fi
done
```

## 9. Security Considerations

### Network Policies
```yaml
# k8s/network-policies.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: brainlens-network-policy
  namespace: brainlens
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: brainlens
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          name: brainlens
  - to: []
    ports:
    - port: 443
      protocol: TCP
  - to: []
    ports:
    - port: 80
      protocol: TCP
```

### Azure AD Integration
```yaml
# k8s/azure-ad-pod-identity.yaml
apiVersion: aadpodidentity.k8s.io/v1
kind: AzureIdentity
metadata:
  name: brainlens-identity
  namespace: brainlens
spec:
  type: 0
  resourceID: /subscriptions/.../resourcegroups/.../providers/Microsoft.ManagedIdentity/userAssignedIdentities/brainlens-identity
  clientID: <client-id>
```

## 10. Scaling and Performance

### Horizontal Pod Autoscaler
```yaml
# k8s/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: image-service-hpa
  namespace: brainlens
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: image-service
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

## Next Steps

1. **Set up Azure resources** (Resource Group, AKS Cluster, ACR)
2. **Configure DNS** for your domain
3. **Set up SSL certificates** with cert-manager
4. **Configure Azure Monitor** for logging and monitoring
5. **Set up CI/CD pipeline** with Azure DevOps or GitHub Actions
6. **Configure backup strategy** for MongoDB
7. **Set up disaster recovery** procedures

This deployment provides a production-ready AKS setup with proper service isolation, monitoring, and scalability for the BrainLens application.