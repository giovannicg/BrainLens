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
- **Image Service** (Puerto 8002): Manejo de imágenes médicas
- **Annotation Service** (Puerto 8003): Gestión de anotaciones

### Frontend

- **Frontend Service** (Puerto 3000): Aplicación React con TypeScript

### Base de Datos

- **MongoDB** (Puerto 27017): Almacenamiento de datos

## 🛠️ Tecnologías

### Backend
- **Python** con FastAPI
- **MongoDB** para persistencia de datos
- **Docker** para containerización

### Frontend
- **React** con TypeScript
- **React Router** para navegación
- **Axios** para comunicación con APIs
- **CSS3** con diseño responsive

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

### Despliegue en AWS EKS (Sin Dominio Personalizado)

Si despliegas en AWS EKS sin un dominio personalizado:

1. **Después del despliegue**, obtén la URL del LoadBalancer:
```bash
kubectl get ingress brainlens-ingress -n brainlens
```

2. **Accede a tu aplicación** usando la URL del LoadBalancer:
```
http://YOUR_LOADBALANCER_URL
```

3. **URLs de la API**:
```
http://YOUR_LOADBALANCER_URL/api/v1/auth
http://YOUR_LOADBALANCER_URL/api/v1/images
http://YOUR_LOADBALANCER_URL/api/v1/annotations
```

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
# Configuración de MongoDB
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=brainlens

# Configuración de almacenamiento
STORAGE_TYPE=local
LOCAL_STORAGE_PATH=./storage

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
   - Procesamiento automático

3. **Análisis y Anotaciones**
   - Crear anotaciones en imágenes
   - Gestionar estado de anotaciones
   - Búsqueda y filtrado

4. **Dashboard**
   - Estadísticas en tiempo real
   - Actividad reciente
   - Acciones rápidas

## 🔒 Seguridad

- Autenticación JWT
- Validación de datos
- Protección CORS
- Almacenamiento seguro de imágenes

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