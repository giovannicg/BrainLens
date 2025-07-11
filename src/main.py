from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from infrastructure.database import connect_to_mongo, close_mongo_connection, health_check as db_health_check

app = FastAPI(
    title="BrainLens API",
    description="API para el proyecto BrainLens",
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

# Aquí se montarán los routers de los controladores
# from adapters.controllers import router as main_router
# app.include_router(main_router)

@app.get("/")
async def root():
    return {"message": "BrainLens API está funcionando"}

@app.get("/health")
async def health_check():
    """Verificar el estado de la API y la base de datos"""
    db_status = await db_health_check()
    return {
        "api": "healthy",
        "database": db_status
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 