import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from dotenv import load_dotenv

from infrastructure.database import database
from adapters.controllers.annotation_controller import router as annotation_router

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await database.connect_db()
    print("🚀 Annotation Service iniciado")
    yield
    # Shutdown
    await database.close_db()
    print("👋 Annotation Service cerrado")

# Crear aplicación FastAPI
app = FastAPI(
    title="BrainLens Annotation Service",
    description="Servicio para gestión de anotaciones médicas",
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
app.include_router(annotation_router, prefix="/api/v1")

@app.get("/")
async def root():
    """Endpoint raíz del servicio"""
    return {
        "service": "BrainLens Annotation Service",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "create": "/api/v1/annotations/",
            "list": "/api/v1/annotations/",
            "get_by_id": "/api/v1/annotations/{annotation_id}",
            "get_by_status": "/api/v1/annotations/status/{status}",
            "get_by_category": "/api/v1/annotations/category/{category}",
            "pending_reviews": "/api/v1/annotations/pending/reviews",
            "update": "/api/v1/annotations/{annotation_id}",
            "review": "/api/v1/annotations/{annotation_id}/review",
            "delete": "/api/v1/annotations/{annotation_id}"
        }
    }

@app.get("/health")
async def health_check():
    """Endpoint de verificación de salud del servicio"""
    return {
        "status": "healthy",
        "service": "annotation-service",
        "database": "connected" if database.client else "disconnected"
    }

if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8003"))
    debug = os.getenv("DEBUG", "false").lower() == "true"
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=debug
    )
