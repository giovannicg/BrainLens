# BrainLens

Plataforma avanzada para análisis y anotación de imágenes médicas cerebrales utilizando inteligencia artificial.

## 🚀 Características

- **Análisis Avanzado**: Algoritmos de IA para detectar anomalías y patrones en imágenes cerebrales
- **Anotaciones Precisas**: Crear y gestionar anotaciones detalladas con herramientas intuitivas
- **Dashboard Interactivo**: Visualiza estadísticas y resultados en tiempo real
- **Seguridad Garantizada**: Protección de datos médicos con estándares de seguridad avanzados
- **Arquitectura Microservicios**: Diseño modular y escalable

## 🏗️ Arquitectura

El proyecto está estructurado como una aplicación de microservicios:

### Servicios Backend

- **Auth Service** (Puerto 8001): Gestión de autenticación y usuarios
- **Image Service** (Puerto 8002): Manejo de imágenes médicas y validación con AWS Bedrock
- **Annotation Service** (Puerto 8003): Gestión de anotaciones
- **Colab Service** (Puerto 8004): Predicción de modelos de IA para análisis de imágenes

### Frontend

- **Frontend Service** (Puerto 3000): Aplicación React con TypeScript

### Base de Datos y Almacenamiento

- **MongoDB Atlas**: Base de datos en la nube para persistencia de datos
- **AWS S3**: Almacenamiento de imágenes médicas
- **AWS Bedrock**: Servicio de IA para validación de imágenes médicas

## 🛠️ Tecnologías

### Backend
- **Python** con FastAPI y Flask
- **MongoDB Atlas** para persistencia de datos
- **AWS Bedrock** para validación de imágenes médicas
- **AWS S3** para almacenamiento de imágenes
- **Docker** para containerización
- **Kubernetes (EKS)** para orquestación de contenedores

### Frontend
- **React** con TypeScript
- **React Router** para navegación
- **Axios** para comunicación con APIs
- **CSS3** con diseño responsive

### Infraestructura
- **AWS EKS** (Elastic Kubernetes Service)
- **AWS ECR** (Elastic Container Registry)
- **AWS Load Balancer** para tráfico externo
- **NGINX Ingress Controller** para enrutamiento
- **Terraform** para infraestructura como código

## 📦 Instalación

### Prerrequisitos

- Docker y Docker Compose
- Node.js 18+ (para desarrollo local del frontend)

### Ejecución con Docker

1. Clona el repositorio:
```bash
git clone <repository-url>
cd BrainLens
```

2. Copia el archivo de variables de entorno:
```bash
cp env.example .env
```

3. Ejecuta todos los servicios:
```bash
docker-compose up -d
```

4. Accede a la aplicación:
- Frontend: http://localhost:3000
- Auth Service: http://localhost:8001
- Image Service: http://localhost:8002
- Annotation Service: http://localhost:8003
- Colab Service: http://localhost:8004

### Despliegue en AWS EKS

#### Prerrequisitos para AWS EKS

- AWS CLI configurado
- kubectl instalado
- Terraform (opcional, para infraestructura)
- Docker para construir imágenes

#### Configuración de Infraestructura

1. **Crear cluster EKS con Terraform**:
```bash
cd infra/terraform
terraform init
terraform plan
terraform apply
```

2. **Configurar kubectl para EKS**:
```bash
aws eks update-kubeconfig --region eu-north-1 --name brainlens-eks
```

3. **Desplegar con GitHub Actions**:
   - Configura los secrets en GitHub:
     - `AWS_ACCESS_KEY_ID`
     - `AWS_SECRET_ACCESS_KEY`
     - `MONGODB_URI`
     - `JWT_SECRET`
   - El workflow automáticamente construye y despliega las imágenes

#### Acceso a la Aplicación

1. **Obtener la URL del LoadBalancer**:
```bash
kubectl get ingress brainlens-ingress -n brainlens
```

2. **Acceder a la aplicación**:
```
http://YOUR_LOADBALANCER_URL
```

3. **URLs de la API**:
```
http://YOUR_LOADBALANCER_URL/api/v1/auth
http://YOUR_LOADBALANCER_URL/api/v1/images
http://YOUR_LOADBALANCER_URL/api/v1/annotations
http://YOUR_LOADBALANCER_URL/api/v1/colab
```

#### Servicios AWS Utilizados

- **EKS**: Cluster de Kubernetes gestionado
- **ECR**: Registro de contenedores Docker
- **S3**: Almacenamiento de imágenes médicas
- **Bedrock**: Validación de imágenes con IA
- **Load Balancer**: Tráfico externo hacia la aplicación

### Desarrollo Local

Para desarrollo local del frontend:

```bash
cd services/frontend-service
npm install
npm start
```

## 📁 Estructura del Proyecto

```
BrainLens/
├── docker-compose.yml
├── env.example
├── requirements.txt
├── k8s/                    # Manifiestos de Kubernetes
│   ├── namespace.yaml
│   ├── configmap.yaml
│   ├── secret.yaml
│   ├── auth-service.yaml
│   ├── image-service.yaml
│   ├── annotation-service.yaml
│   ├── colab-service.yaml
│   ├── frontend-service.yaml
│   ├── ingress.yaml
│   └── network-policies.yaml
├── infra/                  # Infraestructura como código
│   └── terraform/
│       ├── main.tf
│       ├── variables.tf
│       └── outputs.tf
├── .github/               # CI/CD con GitHub Actions
│   └── workflows/
│       └── deploy-eks.yaml
└── services/
    ├── auth-service/
    │   ├── Dockerfile
    │   ├── requirements.txt
    │   └── src/
    │       ├── adapters/
    │       ├── domain/
    │       ├── infrastructure/
    │       ├── usecases/
    │       └── main.py
    ├── image-service/
    │   ├── Dockerfile
    │   └── src/
    │       ├── adapters/
    │       ├── domain/
    │       ├── infrastructure/
    │       ├── usecases/
    │       └── main.py
    ├── annotation-service/
    │   ├── Dockerfile
    │   └── src/
    │       ├── adapters/
    │       ├── domain/
    │       ├── infrastructure/
    │       ├── usecases/
    │       └── main.py
    ├── colab-service/
    │   ├── Dockerfile
    │   └── src/
    │       └── main.py
    └── frontend-service/
        ├── Dockerfile
        ├── nginx.conf
        ├── package.json
        └── src/
            ├── components/
            ├── pages/
            ├── services/
            ├── types/
            └── App.tsx
```

## 🔧 Configuración

### Variables de Entorno

Copia `env.example` a `.env` y configura las variables:

```env
# Configuración de MongoDB Atlas
MONGODB_URL=mongodb+srv://username:password@cluster.mongodb.net/brainlens
DATABASE_NAME=brainlens

# Configuración de almacenamiento
STORAGE_TYPE=s3
S3_BUCKET=brainlens-storage-v8q35chb
S3_PREFIX=images

# Configuración de AWS
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_DEFAULT_REGION=eu-north-1

# Configuración de IA
VLM_PROVIDER=bedrock
BEDROCK_MODEL_ID=amazon.nova-lite-v1:0

# Configuración del servidor
HOST=0.0.0.0
PORT=8000
DEBUG=true
```

## 🚀 Uso

### Funcionalidades Principales

1. **Registro e Inicio de Sesión**
   - Crear cuenta de usuario
   - Autenticación segura

2. **Subida de Imágenes**
   - Drag & drop de imágenes médicas
   - Soporte para formatos JPG, PNG, DICOM
   - Validación automática con AWS Bedrock
   - Almacenamiento seguro en AWS S3

3. **Análisis y Anotaciones**
   - Crear anotaciones en imágenes
   - Gestionar estado de anotaciones
   - Búsqueda y filtrado

4. **Predicción con IA**
   - Análisis automático de imágenes cerebrales
   - Modelos de machine learning para detección de anomalías
   - Resultados de predicción en tiempo real

5. **Dashboard**
   - Estadísticas en tiempo real
   - Actividad reciente
   - Acciones rápidas

## 🔒 Seguridad

- Autenticación JWT
- Validación de datos
- Protección CORS
- Almacenamiento seguro de imágenes en AWS S3
- Credenciales AWS gestionadas por Kubernetes Secrets
- Network Policies para aislamiento de servicios

## 🔍 Monitoreo y Troubleshooting

### Comandos Útiles para EKS

```bash
# Ver estado de los pods
kubectl get pods -n brainlens

# Ver logs de un servicio
kubectl logs -n brainlens -l app=image-service --tail=50

# Describir un pod para ver eventos
kubectl describe pod -n brainlens <pod-name>

# Reiniciar un deployment
kubectl rollout restart deployment/image-service -n brainlens

# Ver servicios y endpoints
kubectl get svc,ep -n brainlens

# Ver ingress y load balancer
kubectl get ingress -n brainlens
```

### Problemas Comunes

1. **ImagePullBackOff**: Verificar que las imágenes estén en ECR y las credenciales sean correctas
2. **CrashLoopBackOff**: Revisar logs del pod para identificar errores de aplicación
3. **Pending**: Verificar recursos disponibles en el cluster
4. **504 Gateway Timeout**: Aumentar timeouts en el Ingress para operaciones largas

## 🤝 Contribución

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📝 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## 📞 Soporte

Para soporte técnico o preguntas, contacta al equipo de desarrollo.

---

**BrainLens** - Revolucionando el análisis de imágenes médicas con IA