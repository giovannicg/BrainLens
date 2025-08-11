# 🧠 BrainLens - Procesamiento en Background

Este servicio permite subir imágenes de resonancia magnética (MRI) y procesarlas automáticamente en background para detectar tumores cerebrales.

## 🚀 Características

- **Subida inmediata**: Las imágenes se guardan instantáneamente
- **Procesamiento asíncrono**: El análisis de IA se ejecuta en background
- **Estados de procesamiento**: pending → processing → completed/failed
- **API REST**: Para consultar el estado del procesamiento
- **Análisis automático**: Detección de tumores usando EfficientNetB3
- **Monitoreo**: Flower para visualizar tareas en tiempo real

## 📋 Requisitos

- Python 3.8+
- Redis (para Celery)
- TensorFlow 2.16.0+
- MongoDB
- Modelo entrenado (`modelo_multiclase.h5`)
- Docker y Docker Compose

## 🛠️ Instalación

### Opción 1: Docker (Recomendado)

#### 1. Copiar el modelo entrenado

```bash
# Desde el directorio raíz del proyecto
cp modelo_multiclase.h5 .
```

#### 2. Ejecutar con Docker Compose

```bash
# Desde el directorio raíz del proyecto
docker-compose up -d

# Ver estado de los servicios
docker-compose ps

# Ver logs en tiempo real
docker-compose logs -f
```

#### 3. Acceder a los servicios

- **API Service**: http://localhost:8002
- **API Docs**: http://localhost:8002/docs
- **Health Check**: http://localhost:8002/health
- **Flower (Monitoreo)**: http://localhost:5555
- **Frontend**: http://localhost:3000

### Opción 2: Instalación Local

#### 1. Instalar dependencias

```bash
cd services/image-service
pip install -r requirements.txt
```

#### 2. Configurar variables de entorno

Crear archivo `.env`:

```env
MONGODB_URL=mongodb://admin:password@localhost:27017
DATABASE_NAME=brainlens
MODEL_PATH=modelo_multiclase.h5
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
HOST=0.0.0.0
PORT=8002
DEBUG=false
```

#### 3. Iniciar Redis

```bash
# Instalar Redis (macOS)
brew install redis
brew services start redis

# O usar Docker
docker run -d --name redis -p 6379:6379 redis:alpine
```

#### 4. Copiar el modelo entrenado

```bash
# Copiar el modelo desde el directorio raíz
cp ../../modelo_multiclase.h5 .
```

#### 5. Ejecutar servicios

```bash
# Terminal 1: Worker de Celery
python start_celery_worker.py

# Terminal 2: API Service
python -m src.main
```

## 📡 API Endpoints

### Subir imagen (inicia procesamiento automático)

```http
POST /api/v1/images/upload?user_id={user_id}
Content-Type: multipart/form-data

file: [archivo de imagen]
custom_name: string (opcional)
```

**Respuesta:**
```json
{
  "message": "Imagen subida exitosamente. El análisis de tumores se está procesando en background.",
  "image": {
    "id": "64f8a1b2c3d4e5f6a7b8c9d0",
    "filename": "imagen.jpg",
    "processing_status": "pending",
    "metadata": {
      "processing_started": "2024-01-15T10:30:00Z",
      "processing_status": "pending"
    }
  },
  "processing_status": "pending"
}
```

### Consultar estado del procesamiento

```http
GET /api/v1/images/{image_id}/processing-status
```

**Respuesta (pending):**
```json
{
  "image_id": "64f8a1b2c3d4e5f6a7b8c9d0",
  "status": "pending",
  "message": "La imagen está en cola para procesamiento",
  "prediction": null,
  "processing_started": "2024-01-15T10:30:00Z",
  "processing_completed": null
}
```

**Respuesta (processing):**
```json
{
  "image_id": "64f8a1b2c3d4e5f6a7b8c9d0",
  "status": "processing",
  "message": "La imagen se está procesando actualmente",
  "prediction": null,
  "processing_started": "2024-01-15T10:30:00Z",
  "processing_completed": null
}
```

**Respuesta (completed):**
```json
{
  "image_id": "64f8a1b2c3d4e5f6a7b8c9d0",
  "status": "completed",
  "message": "El análisis se ha completado exitosamente",
  "prediction": {
    "es_tumor": true,
    "clase_predicha": "glioma",
    "confianza": 0.89,
    "probabilidades": {
      "glioma": 0.89,
      "meningioma": 0.05,
      "no_tumor": 0.03,
      "pituitary": 0.03
    },
    "recomendacion": "⚠️ Se ha detectado un tumor cerebral. Se recomienda consultar con un médico especialista inmediatamente."
  },
  "processing_started": "2024-01-15T10:30:00Z",
  "processing_completed": "2024-01-15T10:31:00Z"
}
```

### Obtener lista de imágenes

```http
GET /api/v1/images/?user_id={user_id}&skip=0&limit=100
```

### Obtener imágenes por estado

```http
GET /api/v1/images/status/{status}
```

Estados disponibles: `pending`, `processing`, `completed`, `failed`

## 🔍 Ejemplo de Uso

### 1. Subir una imagen

```bash
curl -X POST "http://localhost:8002/api/v1/images/upload?user_id=usuario123" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@mi_imagen_mri.jpg"
```

### 2. Consultar estado del procesamiento

```bash
curl "http://localhost:8002/api/v1/images/64f8a1b2c3d4e5f6a7b8c9d0/processing-status"
```

### 3. Obtener imágenes completadas

```bash
curl "http://localhost:8002/api/v1/images/status/completed"
```

## 🔄 Estados del Procesamiento

| Estado | Descripción |
|--------|-------------|
| `pending` | Imagen en cola para procesamiento |
| `processing` | Imagen siendo procesada por el modelo |
| `completed` | Análisis completado exitosamente |
| `failed` | Error en el procesamiento |

## 🧠 Tipos de Tumores Detectados

| Clase | Descripción |
|-------|-------------|
| `glioma` | Tumor que se origina en las células gliales |
| `meningioma` | Tumor que se origina en las meninges |
| `no_tumor` | Sin presencia de tumor |
| `pituitary` | Tumor en la glándula pituitaria |

## 🐳 Docker Compose

### Servicios Integrados

El `image-service` se integra con el `docker-compose.yml` principal del proyecto:

- **mongodb**: Base de datos principal
- **redis**: Broker de mensajes para Celery
- **auth-service**: Autenticación de usuarios
- **image-service**: API REST para imágenes
- **image-service-worker**: Worker de Celery para procesamiento
- **flower**: Monitoreo de tareas de Celery
- **annotation-service**: Servicio de anotaciones
- **frontend-service**: Interfaz web

### Comandos Útiles

```bash
# Iniciar todos los servicios
docker-compose up -d

# Ver estado de los servicios
docker-compose ps

# Ver logs de todos los servicios
docker-compose logs -f

# Ver logs específicos del image-service
docker-compose logs -f image-service

# Ver logs del worker
docker-compose logs -f image-service-worker

# Detener todos los servicios
docker-compose down

# Reconstruir servicios
docker-compose build --no-cache

# Reiniciar servicios específicos
docker-compose restart image-service image-service-worker
```

### Estructura de Red

```
brainlens-network:
├── mongodb:27017
├── redis:6379
├── auth-service:8001
├── image-service:8002
├── image-service-worker
├── flower:5555
├── annotation-service:8003
└── frontend-service:3000
```

## 🔧 Configuración Avanzada

### Variables de entorno adicionales

```env
# Configuración de Celery
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
CELERY_WORKER_CONCURRENCY=2
CELERY_TASK_TIME_LIMIT=300

# Configuración del modelo
MODEL_PATH=modelo_multiclase.h5
IMG_SIZE=300
BATCH_SIZE=1

# Configuración de logging
LOG_LEVEL=INFO
LOG_FILE=image_service.log
```

### Monitoreo con Flower

Flower proporciona una interfaz web para monitorear:

- Tareas activas
- Tareas completadas
- Tareas fallidas
- Estadísticas de workers
- Colas de tareas

Acceder a: http://localhost:5555

### Monitoreo de tareas

```bash
# Ver tareas en cola
docker exec brainlens-image-worker celery -A src.tasks.tumor_analysis_tasks inspect active

# Ver estadísticas
docker exec brainlens-image-worker celery -A src.tasks.tumor_analysis_tasks inspect stats

# Ver workers activos
docker exec brainlens-image-worker celery -A src.tasks.tumor_analysis_tasks inspect ping
```

## 🐛 Solución de Problemas

### Error: "Redis connection failed"

```bash
# Verificar que Redis esté ejecutándose
docker-compose ps redis

# Reiniciar Redis
docker-compose restart redis
```

### Error: "Model not found"

```bash
# Verificar que el modelo existe en el directorio raíz
ls -la modelo_multiclase.h5

# Copiar el modelo si no existe
cp ../../modelo_multiclase.h5 .
```

### Error: "Celery worker not responding"

```bash
# Verificar logs del worker
docker-compose logs image-service-worker

# Reiniciar el worker
docker-compose restart image-service-worker
```

### Error: "Docker services not starting"

```bash
# Verificar logs
docker-compose logs

# Reconstruir imágenes
docker-compose build --no-cache

# Limpiar y reiniciar
docker-compose down -v
docker-compose up -d
```

## 📊 Monitoreo

### Health Check

```bash
curl http://localhost:8002/health
```

### Documentación API

```bash
# Abrir en navegador
http://localhost:8002/docs
```

### Flower Dashboard

```bash
# Abrir en navegador
http://localhost:5555
```

## ⚠️ Consideraciones Importantes

1. **Solo para investigación**: Este sistema es para fines educativos
2. **No reemplaza diagnóstico médico**: Siempre consultar con profesionales
3. **Calidad de imagen**: Mejores resultados con imágenes de alta calidad
4. **Procesamiento asíncrono**: Las predicciones pueden tardar varios segundos
5. **Recursos**: El modelo requiere memoria y CPU significativos
6. **Integración**: El servicio se integra con la arquitectura de microservicios existente

## 🤝 Contribución

1. Fork el proyecto
2. Crear una rama para tu feature
3. Commit tus cambios
4. Push a la rama
5. Abrir un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver `LICENSE` para más detalles.
