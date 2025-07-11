from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from infrastructure.database import connect_to_mongo, close_mongo_connection, health_check as db_health_check
from adapters.controllers.auth_controller import router as auth_router
import logging
import os

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

app = FastAPI(
    title="BrainLens Auth Service",
    description="Servicio de autenticación para BrainLens",
    version="1.0.0"
)

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configurar según necesidades de producción
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Evento de inicio de la aplicación"""
    await connect_to_mongo()

@app.on_event("shutdown")
async def shutdown_event():
    """Evento de cierre de la aplicación"""
    await close_mongo_connection()

# Incluir routers
app.include_router(auth_router)

@app.get("/")
async def root():
    return {
        "message": "BrainLens Auth Service está funcionando",
        "version": "1.0.0",
        "service": "auth"
    }

@app.get("/health")
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
