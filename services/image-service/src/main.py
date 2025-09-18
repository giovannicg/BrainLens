import os
import time
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from dotenv import load_dotenv

from infrastructure.database import database
from adapters.controllers.image_controller import router as image_router

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await database.connect_db()
    print("🚀 Image Service iniciado")
    yield
    # Shutdown
    await database.close_db()
    print("👋 Image Service cerrado")

# Crear aplicación FastAPI
app = FastAPI(
    title="BrainLens Image Service",
    description="Servicio para gestión de imágenes médicas con análisis de tumores en background",
    version="1.0.0",
    lifespan=lifespan
)

# Configuración dinámica de CORS
def get_cors_origins():
    """Configuración dinámica de CORS según el entorno"""
    environment = os.getenv("ENVIRONMENT", "development")
    alb_dns = os.getenv("ALB_DNS_NAME", "")

    if environment == "production" and alb_dns:
        return [f"http://{alb_dns}", f"https://{alb_dns}"]
    else:
        return ["http://localhost:3000", "http://127.0.0.1:3000"]

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware para headers de caché
@app.middleware("http")
async def add_cache_headers(request: Request, call_next):
    response = await call_next(request)
    
    # Headers de seguridad
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    
    # Configurar caché según el tipo de endpoint
    path = request.url.path
    
    if path.startswith("/api/v1/images/download/"):
        # Imágenes descargables - caché largo
        response.headers["Cache-Control"] = "public, max-age=31536000"  # 1 año
        response.headers["Expires"] = "Thu, 31 Dec 2025 23:59:59 GMT"
    elif path.startswith("/api/v1/images/") and request.method == "GET":
        # Metadatos de imágenes - caché corto
        response.headers["Cache-Control"] = "public, max-age=300"  # 5 minutos
    elif path == "/api/v1/images/health":
        # Health check - sin caché
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    else:
        # APIs dinámicas - sin caché
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
    
    return response

# Incluir routers
app.include_router(image_router, prefix="/api/v1")

@app.get("/")
async def root():
    """Endpoint raíz del servicio"""
    return {
        "service": "BrainLens Image Service",
        "version": "1.0.0",
        "status": "running",
        "description": "Servicio para gestión de imágenes médicas con análisis automático de tumores cerebrales",
        "endpoints": {
            "upload": "/api/v1/images/upload",
            "list": "/api/v1/images/",
            "get_by_id": "/api/v1/images/{image_id}",
            "get_by_status": "/api/v1/images/status/{status}",
            "delete": "/api/v1/images/{image_id}",
            "processing_status": "/api/v1/images/{image_id}/processing-status"
        },
        "processing_states": {
            "pending": "Imagen en cola para procesamiento",
            "processing": "Imagen siendo procesada",
            "completed": "Análisis completado",
            "failed": "Error en el procesamiento"
        },
        "ai_features": {
            "tumor_detection": "Análisis automático de tumores cerebrales usando EfficientNetB3",
            "background_processing": "Procesamiento asíncrono con Celery",
            "supported_classes": ["glioma", "meningioma", "no_tumor", "pituitary"]
        }
    }

@app.get("/health")
async def health_check():
    """Endpoint de verificación de salud del servicio"""
    return {
        "status": "healthy",
        "service": "image-service",
        "database": "connected" if database.client else "disconnected",
        "background_processing": "enabled"
    }

# Health bajo prefijo de API para ALB/productivo
@app.get("/api/v1/images/health")
async def health_check_api_v1():
    return {
        "status": "healthy",
        "service": "image-service",
        "database": "connected" if database.client else "disconnected"
    }

if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8002"))
    debug = os.getenv("DEBUG", "false").lower() == "true"
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=debug
    )
