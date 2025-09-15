import os
from fastapi import FastAPI, HTTPException
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
        return [f"http://{alb_dns}"]
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
