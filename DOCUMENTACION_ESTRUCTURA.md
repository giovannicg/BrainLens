# 📚 Documentación de Estructura - BrainLens

## 🏗️ Arquitectura General

**BrainLens** es una plataforma avanzada para análisis y anotación de imágenes médicas cerebrales que utiliza inteligencia artificial. La aplicación está diseñada siguiendo una arquitectura de **microservicios** con separación clara de responsabilidades.

### 🎯 Objetivo Principal
Proporcionar una solución completa para el análisis automático de imágenes de resonancia magnética (MRI) cerebrales, detectando tumores y permitiendo anotaciones médicas precisas.

---

## 🏛️ Arquitectura de Microservicios

### 📊 Diagrama de Arquitectura

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Auth Service  │    │  Image Service  │
│   (React)       │◄──►│   (FastAPI)     │◄──►│   (FastAPI)     │
│   Puerto 3000   │    │   Puerto 8001   │    │   Puerto 8002   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Annotation      │    │    MongoDB      │    │     Redis       │
│ Service         │    │   Puerto 27017  │    │   Puerto 6379   │
│ (FastAPI)       │    │                 │    │                 │
│ Puerto 8003     │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                       │
                                │                       │
                                ▼                       ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │   Celery        │    │     Flower      │
                       │   Worker        │    │   Puerto 5555   │
                       │                 │    │                 │
                       └─────────────────┘    └─────────────────┘

                           ▲
                           │
                   ┌─────────────────┐
                   │     Ollama      │
                   │  (VLM Docker)   │
                   │  Puerto 11434   │
                   └─────────────────┘
```

---

## 🔧 Servicios Backend

### 1. 🔐 Auth Service (Puerto 8001)

**Propósito**: Gestión completa de autenticación y autorización de usuarios.

#### 📁 Estructura del Servicio
```
services/auth-service/
├── Dockerfile
├── requirements.txt
└── src/
    ├── adapters/          # Controladores y presentación
    ├── domain/            # Lógica de negocio y entidades
    ├── infrastructure/    # Base de datos y configuraciones
    ├── usecases/          # Casos de uso específicos
    └── main.py           # Punto de entrada de la aplicación
```

#### 🚀 Funcionalidades Principales
- **Registro de usuarios**: Creación de cuentas con validación
- **Autenticación**: Login con JWT tokens
- **Gestión de sesiones**: Manejo seguro de sesiones de usuario
- **Autorización**: Control de acceso basado en roles
- **Validación de tokens**: Verificación de autenticación

#### 🔗 Endpoints Principales
- `POST /register` - Registro de nuevos usuarios
- `POST /login` - Autenticación de usuarios
- `POST /logout` - Cierre de sesión
- `GET /profile` - Información del perfil de usuario
- `GET /health` - Verificación de estado del servicio

#### 🛠️ Tecnologías Utilizadas
- **FastAPI**: Framework web moderno y rápido
- **MongoDB**: Base de datos NoSQL para usuarios
- **JWT**: Tokens de autenticación seguros
- **Pydantic**: Validación de datos
- **Docker**: Containerización del servicio

---

### 2. 🖼️ Image Service (Puerto 8002)

**Propósito**: Gestión completa de imágenes médicas con análisis automático de tumores cerebrales usando IA.

#### 📁 Estructura del Servicio
```
services/image-service/
├── Dockerfile
├── requirements.txt
├── start_celery_worker.py
├── README_BACKGROUND_PROCESSING.md
└── src/
    ├── adapters/          # Controladores de API
    ├── domain/            # Entidades y lógica de negocio
    ├── infrastructure/    # Base de datos y almacenamiento
    ├── usecases/          # Casos de uso de imágenes
    ├── tasks/             # Tareas de Celery para procesamiento
    │   ├── celery_config.py
    │   └── tumor_analysis_tasks.py
    └── main.py           # Punto de entrada
```

#### 🚀 Funcionalidades Principales
- **Subida de imágenes**: Soporte para formatos JPG, PNG, DICOM
- **Almacenamiento seguro**: Gestión de archivos médicos
- **Análisis automático**: Detección de tumores con IA
- **Procesamiento asíncrono**: Análisis en background con Celery
- **Estados de procesamiento**: Seguimiento del estado de análisis
- **Chat visual**: Conversación sobre una imagen con un modelo visión-lenguaje (VLM)

#### 🧠 Análisis de IA
- **Modelo**: EfficientNetB3 entrenado para detección de tumores
- **Clases detectadas**: 
  - `glioma` - Tumor glial
  - `meningioma` - Tumor meníngeo
  - `no_tumor` - Sin tumor
  - `pituitary` - Tumor pituitario
- **Procesamiento**: Análisis automático en background

#### 🔗 Endpoints Principales
- `POST /api/v1/images/upload` - Subida de imágenes
- `GET /api/v1/images/` - Lista de imágenes
- `GET /api/v1/images/{image_id}` - Obtener imagen específica
- `GET /api/v1/images/status/{status}` - Filtrar por estado
- `DELETE /api/v1/images/{image_id}` - Eliminar imagen
- `GET /api/v1/images/download/{image_id}` - Descargar imagen
- `GET /api/v1/images/{image_id}/processing-status` - Estado de procesamiento

#### 💬 Chat Visual: Diseño y Persistencia
- **Repositorio**: `MongoChatRepository` (colección `image_chats`)
- **Entidad**: `ChatMessage` con `image_id`, `user_id`, `role` (`user|assistant`), `content`, `timestamp`
- **Gateway VLM**: `VisionLanguageGateway` con soporte `Ollama` (por defecto) y `OpenAI`
- **ENV**:
  - `VLM_PROVIDER=ollama|openai`
  - `VLM_MODEL=minicpm-v` (recomendado en español)
  - `OLLAMA_BASE_URL=http://ollama:11434`
  - `VLM_SYSTEM_PROMPT` y `VLM_FORCE_SPANISH=true` para forzar respuestas en español

#### 🛠️ Tecnologías Utilizadas
- **FastAPI**: API REST moderna
- **TensorFlow**: Framework de IA para análisis
- **Celery**: Procesamiento asíncrono
- **Redis**: Broker de mensajes para Celery
- **MongoDB**: Almacenamiento de metadatos
- **Pillow**: Procesamiento de imágenes

---

### 3. ✏️ Annotation Service (Puerto 8003)

**Propósito**: Gestión completa de anotaciones médicas en imágenes cerebrales.

#### 📁 Estructura del Servicio
```
services/annotation-service/
├── Dockerfile
├── requirements.txt
└── src/
    ├── adapters/          # Controladores de API
    ├── domain/            # Entidades de anotaciones
    ├── infrastructure/    # Base de datos
    ├── usecases/          # Casos de uso de anotaciones
    ├── config.py          # Configuración del servicio
    └── main.py           # Punto de entrada
```

#### 🚀 Funcionalidades Principales
- **Creación de anotaciones**: Marcado de regiones en imágenes
- **Gestión de estados**: Control del flujo de trabajo de anotaciones
- **Categorización**: Clasificación de tipos de anotaciones
- **Revisión**: Sistema de aprobación de anotaciones
- **Búsqueda y filtrado**: Consultas avanzadas de anotaciones
- **Historial**: Seguimiento de cambios en anotaciones

#### 🔗 Endpoints Principales
- `POST /api/v1/annotations/` - Crear nueva anotación
- `GET /api/v1/annotations/` - Lista de anotaciones
- `GET /api/v1/annotations/{annotation_id}` - Obtener anotación específica
- `GET /api/v1/annotations/status/{status}` - Filtrar por estado
- `GET /api/v1/annotations/category/{category}` - Filtrar por categoría
- `GET /api/v1/annotations/pending/reviews` - Anotaciones pendientes de revisión
- `PUT /api/v1/annotations/{annotation_id}` - Actualizar anotación
- `POST /api/v1/annotations/{annotation_id}/review` - Revisar anotación
- `DELETE /api/v1/annotations/{annotation_id}` - Eliminar anotación

#### 🛠️ Tecnologías Utilizadas
- **FastAPI**: API REST para anotaciones
- **MongoDB**: Almacenamiento de datos de anotaciones
- **Pydantic**: Validación de esquemas
- **Docker**: Containerización

---

## 🎨 Frontend Service (Puerto 3000)

**Propósito**: Interfaz de usuario moderna y responsive para interactuar con todos los servicios backend.

#### 📁 Estructura del Servicio
```
services/frontend-service/
├── Dockerfile
├── nginx.conf
├── package.json
├── tsconfig.json
└── src/
    ├── components/        # Componentes reutilizables
    ├── pages/            # Páginas principales
    ├── services/         # Servicios de API
    ├── contexts/         # Contextos de React
    ├── hooks/            # Hooks personalizados
    ├── types/            # Definiciones de TypeScript
    ├── App.tsx           # Componente principal
    └── index.tsx         # Punto de entrada
```

#### 🚀 Funcionalidades Principales
- **Autenticación**: Login y registro de usuarios
- **Dashboard**: Panel principal con estadísticas
- **Subida de imágenes**: Interfaz drag & drop
- **Visualización**: Galería de imágenes médicas
- **Anotaciones**: Herramientas de marcado en imágenes
- **Gestión**: Administración de anotaciones y estados
- **Responsive**: Diseño adaptable a diferentes dispositivos

#### 📱 Páginas Principales
- **Home** (`/`): Página de bienvenida
- **Login** (`/login`): Autenticación de usuarios
- **Register** (`/register`): Registro de nuevos usuarios
- **Dashboard** (`/dashboard`): Panel principal con estadísticas
- **ImageUpload** (`/upload`): Subida de imágenes médicas
- **Images** (`/images`): Galería de imágenes
- **Annotations** (`/annotations`): Gestión de anotaciones
- **ImageAnnotation** (`/annotate/:imageId`): Herramienta de anotación
- **ImageChat** (`/chat/:imageId`): Chat visual tipo ChatGPT/Perplexity con vista previa, sugerencias y envío optimista.

#### 🛠️ Tecnologías Utilizadas
- **React**: Framework de interfaz de usuario
- **TypeScript**: Tipado estático para mayor seguridad
- **React Router**: Navegación entre páginas
- **Axios**: Cliente HTTP para APIs
- **CSS3**: Estilos modernos y responsive
- **Nginx**: Servidor web y proxy reverso

---

## 🗄️ Infraestructura de Datos

### 1. 📊 MongoDB (Puerto 27017)

**Propósito**: Base de datos principal para todos los servicios.

#### 🗂️ Colecciones Principales
- **users**: Información de usuarios y autenticación
- **images**: Metadatos de imágenes médicas
- **annotations**: Datos de anotaciones médicas
- **processing_tasks**: Estado de tareas de procesamiento

#### 🔧 Configuración
- **Usuario**: admin
- **Contraseña**: password
- **Base de datos**: brainlens
- **Persistencia**: Volumen Docker para datos

### 2. 🔄 Redis (Puerto 6379)

**Propósito**: Broker de mensajes para Celery y caché.

#### 🚀 Funcionalidades
- **Message Broker**: Para tareas asíncronas de Celery
- **Result Backend**: Almacenamiento de resultados de tareas
- **Caché**: Mejora de rendimiento para consultas frecuentes

---

## ⚙️ Procesamiento Asíncrono

### 🔄 Celery Worker

**Propósito**: Ejecución de tareas pesadas en background.

#### 🧠 Tareas Principales
- **Análisis de tumores**: Procesamiento de imágenes con IA
- **Preparación de datos**: Normalización y preprocesamiento
- **Generación de reportes**: Creación de resultados de análisis

#### 📊 Monitoreo con Flower (Puerto 5555)

**Propósito**: Interfaz web para monitorear tareas de Celery.

#### 🚀 Funcionalidades
- **Estado de tareas**: Visualización en tiempo real
- **Métricas**: Estadísticas de procesamiento
- **Logs**: Registros de ejecución
- **Control**: Cancelación y reinicio de tareas

---

## 🐳 Containerización con Docker

### 📦 Servicios Containerizados

1. **mongodb**: Base de datos MongoDB
2. **redis**: Broker de mensajes Redis
3. **auth-service**: Servicio de autenticación
4. **image-service**: Servicio de imágenes
5. **image-service-worker**: Worker de Celery
6. **flower**: Monitoreo de Celery
7. **annotation-service**: Servicio de anotaciones
8. **frontend-service**: Interfaz de usuario
9. **ollama**: Servidor VLM (modelos visión-lenguaje) para el chat visual

### 🔧 Volúmenes Persistentes
- **mongodb_data**: Datos de MongoDB
- **image_storage**: Almacenamiento de imágenes
- **redis_data**: Datos de Redis

### 🌐 Red Docker
- **brainlens-network**: Red interna para comunicación entre servicios

---

## 🔄 Flujo de Trabajo

### 1. 📤 Subida de Imágenes
```
Usuario → Frontend → Image Service → MongoDB (metadatos)
                                    ↓
                              Almacenamiento local
                                    ↓
                              Celery Task (análisis)
```

### 2. 🧠 Análisis Automático
```
Celery Worker → Carga modelo IA → Procesa imagen → 
Actualiza estado → MongoDB (resultados)
```

### 3. ✏️ Creación de Anotaciones
```
Usuario → Frontend → Annotation Service → 
MongoDB (anotaciones) → Actualiza estado
```

### 4. 🔐 Autenticación
```
Usuario → Frontend → Auth Service → 
JWT Token → Validación en todos los servicios
```

---

## 🛡️ Seguridad

### 🔐 Medidas Implementadas
- **JWT Tokens**: Autenticación segura
- **CORS**: Control de acceso entre dominios
- **Validación de datos**: Con Pydantic
- **Almacenamiento seguro**: Imágenes médicas protegidas
- **Logs de auditoría**: Seguimiento de acciones

### 🔒 Estándares de Cumplimiento
- **HIPAA**: Preparado para cumplimiento médico
- **GDPR**: Protección de datos personales
- **ISO 27001**: Estándares de seguridad de información

---

## 📈 Escalabilidad

### 🚀 Estrategias de Escalado
- **Microservicios**: Escalado independiente por servicio
- **Procesamiento asíncrono**: Celery workers escalables
- **Base de datos distribuida**: MongoDB con réplicas
- **Caché distribuido**: Redis para mejorar rendimiento
- **Load balancing**: Nginx para distribución de carga

### 📊 Monitoreo y Métricas
- **Health checks**: Verificación de estado de servicios
- **Logs centralizados**: Seguimiento de errores
- **Métricas de rendimiento**: Tiempos de respuesta
- **Alertas**: Notificaciones de problemas

---

## 🚀 Despliegue

### 📋 Requisitos del Sistema
- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **Memoria**: Mínimo 4GB RAM
- **Almacenamiento**: 10GB espacio libre
- **Red**: Conexión a internet para descarga de imágenes

### 🔧 Comandos de Despliegue
```bash
# Clonar repositorio
git clone <repository-url>
cd BrainLens

# Configurar variables de entorno
cp env.example .env

# Ejecutar todos los servicios
docker-compose up -d

# Verificar estado
docker-compose ps

# Ver logs
docker-compose logs -f

# Descargar un modelo VLM multilingüe en Ollama para el chat
docker exec -it brainlens-ollama ollama pull minicpm-v
# Reiniciar image-service para leer variables
docker compose up -d image-service
```

### 🌐 Acceso a Servicios
- **Frontend**: http://localhost:3000
- **Auth Service**: http://localhost:8001
- **Image Service**: http://localhost:8002
- **Annotation Service**: http://localhost:8003
- **Flower (Monitoreo)**: http://localhost:5555
- **MongoDB**: localhost:27017
- **Redis**: localhost:6379
- **Ollama (VLM)**: http://localhost:11434

---

## 🔧 Desarrollo

### 🛠️ Estructura de Desarrollo
- **Clean Architecture**: Separación clara de capas
- **Domain-Driven Design**: Diseño centrado en dominio
- **Test-Driven Development**: Desarrollo guiado por pruebas
- **API-First**: Diseño de APIs antes de implementación

### 📝 Patrones de Diseño
- **Repository Pattern**: Abstracción de acceso a datos
- **Factory Pattern**: Creación de objetos complejos
- **Observer Pattern**: Notificaciones de eventos
- **Strategy Pattern**: Algoritmos intercambiables

---

## 📚 Conclusión

**BrainLens** representa una solución completa y moderna para el análisis de imágenes médicas cerebrales. Su arquitectura de microservicios proporciona:

- ✅ **Escalabilidad**: Crecimiento horizontal y vertical
- ✅ **Mantenibilidad**: Código modular y bien estructurado
- ✅ **Seguridad**: Protección de datos médicos sensibles
- ✅ **Rendimiento**: Procesamiento asíncrono y optimizado
- ✅ **Usabilidad**: Interfaz intuitiva y responsive

La plataforma está diseñada para satisfacer las necesidades del sector médico, proporcionando herramientas avanzadas de IA para el diagnóstico asistido por computadora, mientras mantiene los más altos estándares de seguridad y calidad. 