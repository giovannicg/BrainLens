# Guía de Deploy a Producción - BrainLens

## ✅ Cambios Realizados

### 1. **Configuración CORS Dinámica**
- **Auth Service**: CORS configurado dinámicamente según entorno
- **Image Service**: CORS configurado dinámicamente según entorno  
- **Annotation Service**: CORS configurado dinámicamente según entorno
- **Colab Service**: CORS configurado dinámicamente según entorno

### 2. **Frontend API Configuration**
- URLs de API configuradas dinámicamente
- Soporte para ALB DNS en producción
- Fallback a localhost en desarrollo

### 3. **Variables de Entorno**
- `ENVIRONMENT`: development/production
- `ALB_DNS_NAME`: DNS del Application Load Balancer
- `DEBUG`: false en producción
- `JWT_SECRET_KEY`: Configurado en env.example

### 4. **Terraform Updates**
- Outputs añadidos para ALB DNS
- Variables de entorno actualizadas en task definitions
- DEBUG=false en producción

## 🚀 Pasos para Deploy

### Paso 1: Configurar Variables de Entorno

```bash
# Copiar archivo de ejemplo
cp env.example .env

# Editar .env con tus valores
nano .env
```

**Variables importantes a configurar:**
```bash
# MongoDB Atlas (ya configurado)
MONGODB_URL=mongodb+srv://usuario:password@cluster.mongodb.net/brainlens

# JWT Secret (CAMBIAR EN PRODUCCIÓN)
JWT_SECRET_KEY=tu-secret-super-seguro-aqui

# Entorno
ENVIRONMENT=production
```

### Paso 2: Deploy de Infraestructura

```bash
cd infra/terraform

# Inicializar Terraform
terraform init

# Planificar cambios
terraform plan -var="mongo_url=tu_mongodb_atlas_url"

# Aplicar cambios
terraform apply -var="mongo_url=tu_mongodb_atlas_url"
```

### Paso 3: Obtener DNS del ALB

```bash
# Obtener el DNS del ALB
terraform output alb_dns_name

# Ejemplo de salida:
# brainlens-alb-123456789.eu-north-1.elb.amazonaws.com
```

### Paso 4: Configurar Variables de GitHub

En tu repositorio de GitHub, ve a **Settings > Secrets and variables > Actions** y configura:

**Variables (no secretos):**
- `ECR_FRONTEND_URI`: `123456789.dkr.ecr.eu-north-1.amazonaws.com/brainlens-frontend`
- `ECR_IMAGE_URI`: `123456789.dkr.ecr.eu-north-1.amazonaws.com/brainlens-image`
- `ECR_AUTH_URI`: `123456789.dkr.ecr.eu-north-1.amazonaws.com/brainlens-auth`
- `ECR_COLAB_URI`: `123456789.dkr.ecr.eu-north-1.amazonaws.com/brainlens-colab`
- `ECR_ANNOTATION_URI`: `123456789.dkr.ecr.eu-north-1.amazonaws.com/brainlens-annotation`
- `ECS_CLUSTER_NAME`: `brainlens-cluster`
- `ECS_BACK_SERVICE_NAME`: `brainlens-back-svc`
- `ECS_FRONT_SERVICE_NAME`: `brainlens-front-svc`
- `ECS_AUTH_SERVICE_NAME`: `brainlens-auth-svc`
- `ECS_ANN_SERVICE_NAME`: `brainlens-ann-svc`
- `ECS_COLAB_SERVICE_NAME`: `brainlens-colab-svc`

**Secrets:**
- `AWS_ACCESS_KEY_ID`: Tu access key de AWS
- `AWS_SECRET_ACCESS_KEY`: Tu secret key de AWS

### Paso 5: Deploy Automático

```bash
# Hacer push a main para trigger el deploy
git add .
git commit -m "feat: configuración para producción"
git push origin main
```

El workflow de GitHub Actions se ejecutará automáticamente y:
1. Construirá las imágenes Docker
2. Las subirá a ECR
3. Desplegará los servicios en ECS

### Paso 6: Verificar Deploy

```bash
# Obtener URL del frontend
terraform output frontend_url

# Verificar que los servicios estén corriendo
aws ecs list-services --cluster brainlens-cluster
```

## 🔧 Configuración Post-Deploy

### 1. **Verificar CORS**
Los servicios ahora usan CORS dinámico:
- **Desarrollo**: `http://localhost:3000`
- **Producción**: `http://tu-alb-dns-name.eu-north-1.elb.amazonaws.com`

### 2. **Verificar Variables de Entorno**
En ECS, los servicios tienen:
- `ENVIRONMENT=production`
- `ALB_DNS_NAME=tu-alb-dns-name`
- `DEBUG=false`

### 3. **Monitoreo**
- **Logs**: CloudWatch `/ecs/brainlens`
- **Health Checks**: ALB configurado con health checks
- **Métricas**: ECS metrics en CloudWatch

## 🛠️ Troubleshooting

### Problema: CORS Error
```bash
# Verificar que ALB_DNS_NAME esté configurado
aws ecs describe-services --cluster brainlens-cluster --services brainlens-front-svc
```

### Problema: Servicios no inician
```bash
# Ver logs de ECS
aws logs describe-log-streams --log-group-name /ecs/brainlens
aws logs get-log-events --log-group-name /ecs/brainlens --log-stream-name [stream-name]
```

### Problema: Frontend no carga
```bash
# Verificar que el ALB esté funcionando
curl -I http://tu-alb-dns-name.eu-north-1.elb.amazonaws.com
```

## 📋 Checklist de Producción

- [ ] MongoDB Atlas configurado
- [ ] JWT_SECRET_KEY cambiado
- [ ] Variables de GitHub configuradas
- [ ] Terraform aplicado
- [ ] Deploy automático ejecutado
- [ ] Servicios funcionando
- [ ] Frontend accesible
- [ ] CORS funcionando
- [ ] Logs visibles en CloudWatch

## 💰 Costo Estimado

- **ECS Fargate**: ~$15-30/mes
- **ALB**: ~$16/mes
- **ECR**: ~$1/mes
- **CloudWatch**: ~$5/mes
- **MongoDB Atlas**: $0 (tier gratuito)
- **Total**: ~$35-50/mes

## 🔒 Seguridad

### ✅ Implementado
- CORS específico por entorno
- DEBUG=false en producción
- Variables de entorno seguras
- Usuarios no-root en containers

### ⚠️ Recomendaciones Adicionales
- Configurar HTTPS (certificado SSL)
- Usar AWS Secrets Manager para JWT
- Implementar WAF
- Configurar backup automático

---

**¡Tu aplicación está lista para producción!** 🎉
