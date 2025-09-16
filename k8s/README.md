# BrainLens Kubernetes Manifests

This directory contains all the Kubernetes manifests for deploying BrainLens on AWS EKS.

## 📁 File Structure

```
k8s/
├── namespace.yaml          # BrainLens namespace
├── configmap.yaml          # Environment variables
├── secret.yaml            # Sensitive data (MongoDB, AWS credentials)
├── mongodb-deployment.yaml # MongoDB with persistent storage
├── auth-service.yaml       # Authentication service
├── image-service.yaml      # Image processing service
├── annotation-service.yaml # Annotation management service
├── colab-service.yaml      # AI/ML prediction service
├── frontend-service.yaml   # React frontend
├── ingress.yaml           # NGINX ingress routing
├── hpa.yaml               # Horizontal Pod Autoscalers
└── network-policies.yaml  # Security network policies
```

## 🚀 Deployment

### Prerequisites

1. **AWS CLI** configured with appropriate permissions
2. **kubectl** installed and configured
3. **Terraform** for infrastructure setup
4. **Helm** (optional, for ingress controller)

### Quick Deployment

```bash
# Set environment variables
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_ACCOUNT_ID="your-account-id"

# Run the automated deployment script
./infra/terraform/deploy-eks.sh
```

### Manual Deployment Steps

1. **Create namespace:**
   ```bash
   kubectl apply -f k8s/namespace.yaml
   ```

2. **Create ConfigMap and Secrets:**
   ```bash
   kubectl apply -f k8s/configmap.yaml
   kubectl apply -f k8s/secret.yaml
   ```

3. **Deploy MongoDB:**
   ```bash
   kubectl apply -f k8s/mongodb-deployment.yaml
   ```

4. **Deploy services:**
   ```bash
   kubectl apply -f k8s/auth-service.yaml
   kubectl apply -f k8s/image-service.yaml
   kubectl apply -f k8s/annotation-service.yaml
   kubectl apply -f k8s/colab-service.yaml
   kubectl apply -f k8s/frontend-service.yaml
   ```

5. **Deploy ingress and policies:**
   ```bash
   kubectl apply -f k8s/ingress.yaml
   kubectl apply -f k8s/hpa.yaml
   kubectl apply -f k8s/network-policies.yaml
   ```

## 🔧 Service Configuration

### Environment Variables

All services use the following environment variables:

- `ENVIRONMENT`: Production/development mode
- `DATABASE_NAME`: MongoDB database name
- `MONGODB_URL`: MongoDB connection string
- `AWS_REGION`: AWS region for services
- `VLM_PROVIDER`: AI model provider (bedrock)
- `VLM_TIMEOUT`: AI model timeout

### Service URLs (Internal DNS)

Services communicate using Kubernetes DNS:

- **Auth Service**: `http://auth-service.brainlens.svc.cluster.local:8001`
- **Image Service**: `http://image-service.brainlens.svc.cluster.local:8002`
- **Annotation Service**: `http://annotation-service.brainlens.svc.cluster.local:8003`
- **Colab Service**: `http://colab-service.brainlens.svc.cluster.local:8004`

### Resource Limits

Each service has appropriate resource requests and limits:

- **Frontend**: 128Mi-256Mi RAM, 50-100m CPU
- **Auth/Image/Annotation**: 256Mi-512Mi RAM, 100-200m CPU
- **Colab**: 512Mi-1Gi RAM, 250-500m CPU

## 🔒 Security Features

### Network Policies

- **Default deny-all**: No traffic allowed by default
- **Service-specific rules**: Only authorized communication
- **Ingress restrictions**: Frontend only accessible via ingress
- **Database isolation**: MongoDB only accessible by backend services

### Secrets Management

- **AWS Credentials**: Stored in Kubernetes secrets
- **MongoDB Password**: Auto-generated and stored securely
- **JWT Secrets**: Randomly generated for authentication

## 📊 Monitoring & Scaling

### Horizontal Pod Autoscaling

- **Image Service**: Scales based on CPU (70%) and memory (80%)
- **Frontend Service**: Scales based on CPU (60%)
- **Min/Max replicas**: Configured for cost optimization

### Health Checks

All services include:
- **Liveness probes**: Restart unhealthy containers
- **Readiness probes**: Remove unhealthy pods from service
- **Startup probes**: Handle slow-starting applications

## 🔄 CI/CD Integration

### GitHub Actions

The manifests are designed to work with the CI/CD pipeline:

1. **ECR Build**: Images pushed to Amazon ECR
2. **EKS Deploy**: Automated deployment to EKS
3. **Health Checks**: Post-deployment verification
4. **Rollback**: Automatic rollback on failures

### Image Updates

To update service images:

```bash
# Update image tag in deployment
kubectl set image deployment/auth-service auth-service=YOUR_ECR_URI:latest

# Or edit the manifest
kubectl edit deployment auth-service
```

## 🐛 Troubleshooting

### Common Issues

1. **Image Pull Errors:**
   ```bash
   kubectl describe pod <pod-name>
   # Check ECR permissions and image tags
   ```

2. **Service Communication:**
   ```bash
   kubectl exec -it <pod-name> -- curl http://<service-name>:port/health
   ```

3. **Network Policies:**
   ```bash
   kubectl describe networkpolicy <policy-name>
   ```

### Logs and Debugging

```bash
# View pod logs
kubectl logs -f deployment/<service-name> -n brainlens

# Check service endpoints
kubectl get endpoints -n brainlens

# Debug network policies
kubectl describe networkpolicy -n brainlens
```

## 📈 Performance Optimization

### Resource Optimization

- **Right-sizing**: Appropriate CPU/memory allocation
- **HPA**: Automatic scaling based on usage
- **Storage**: EFS for shared file storage

### Caching Strategies

- **MongoDB indexing**: Optimized for query patterns
- **Image caching**: S3 for static assets
- **Session storage**: Redis (future enhancement)

## 🔧 Maintenance

### Updates

1. **Service Updates:**
   ```bash
   kubectl rollout restart deployment/<service-name>
   ```

2. **Configuration Changes:**
   ```bash
   kubectl edit configmap brainlens-config
   kubectl rollout restart deployment --selector=app
   ```

3. **Secret Rotation:**
   ```bash
   kubectl create secret generic brainlens-secrets --dry-run=client -o yaml | kubectl apply -f -
   ```

### Backup & Recovery

- **Database backups**: Automated via AWS Backup
- **PVC snapshots**: For persistent data
- **Config backups**: Git version control

## 📚 Additional Resources

- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [AWS EKS Best Practices](https://aws.github.io/aws-eks-best-practices/)
- [Helm Charts](https://helm.sh/docs/)
- [Network Policies](https://kubernetes.io/docs/concepts/services-networking/network-policies/)

---

## 🎯 Quick Reference

```bash
# Check deployment status
kubectl get all -n brainlens

# View logs
kubectl logs -f deployment/<service-name> -n brainlens

# Scale deployment
kubectl scale deployment <service-name> --replicas=3 -n brainlens

# Update image
kubectl set image deployment/<service-name> <container-name>=<new-image> -n brainlens

# Restart deployment
kubectl rollout restart deployment/<service-name> -n brainlens