
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from infrastructure.database import database
from adapters.controllers.annotation_controller import router as annotation_router
from config import settings
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


def configure_cors(app: FastAPI):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOW_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

def configure_routers(app: FastAPI):
    app.include_router(annotation_router, prefix="/api/v1")

app = FastAPI(
    title=settings.APP_TITLE,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
    lifespan=lifespan
)
configure_cors(app)
configure_routers(app)

@app.get("/")
async def root():
    """Endpoint raíz del servicio"""
    return {
        "service": settings.APP_TITLE,
        "version": settings.APP_VERSION,
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

# Health bajo prefijo de API para ALB/productivo
@app.get("/api/v1/annotations/health")
async def health_check_api_v1():
    return {
        "status": "healthy",
        "service": "annotation-service",
        "database": "connected" if database.client else "disconnected"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
