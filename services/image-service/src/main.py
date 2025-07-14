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
    description="Servicio para gestión de imágenes médicas",
    version="1.0.0",
    lifespan=lifespan
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar dominios específicos
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
        "endpoints": {
            "upload": "/api/v1/images/upload",
            "list": "/api/v1/images/",
            "get_by_id": "/api/v1/images/{image_id}",
            "get_by_status": "/api/v1/images/status/{status}",
            "delete": "/api/v1/images/{image_id}",
            "download": "/api/v1/images/download/{image_id}"
        }
    }

@app.get("/health")
async def health_check():
    """Endpoint de verificación de salud del servicio"""
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
