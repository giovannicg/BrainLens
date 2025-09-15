import logging
import os
from fastapi import FastAPI
from fastapi import APIRouter
from fastapi.middleware.cors import CORSMiddleware
from .infrastructure.database import connect_to_mongo, close_mongo_connection, health_check as db_health_check
from .adapters.controllers.auth_controller import router as auth_router
from pydantic_settings import BaseSettings

# Configuración centralizada
class Settings(BaseSettings):
    APP_TITLE: str = "BrainLens Auth Service"
    APP_DESCRIPTION: str = "Servicio de autenticación para BrainLens"
    APP_VERSION: str = "1.0.0"
    ALLOW_ORIGINS: list[str] = ["*"]  # Cambiar en producción
    class Config:
        env_file = ".env"

settings = Settings()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

app = FastAPI(
    title=settings.APP_TITLE,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION
)

def configure_cors(app: FastAPI):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOW_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

configure_cors(app)

@app.on_event("startup")
async def startup_event():
    logging.info("Iniciando Auth Service...")
    await connect_to_mongo()

@app.on_event("shutdown")
async def shutdown_event():
    logging.info("Cerrando Auth Service...")
    await close_mongo_connection()

# Montar rutas bajo /api/v1 para entorno productivo
api_v1 = APIRouter(prefix="/api/v1")
api_v1.include_router(auth_router)  # auth_router ya tiene prefix="/auth"
app.include_router(api_v1)

@app.get("/")
async def root():
    return {
        "message": f"{settings.APP_TITLE} está funcionando",
        "version": settings.APP_VERSION,
        "service": "auth"
    }

# Health para ALB: /api/v1/auth/health
@app.get("/api/v1/auth/health")
async def health_check():
    """Verificar el estado de la API y la base de datos"""
    db_status = await db_health_check()
    return {
        "api": "healthy",
        "database": db_status,
        "service": "auth"
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("AUTH_SERVICE_PORT", "8001"))
    uvicorn.run(app, host="0.0.0.0", port=port)
