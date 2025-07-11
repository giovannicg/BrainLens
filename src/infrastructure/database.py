from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from typing import AsyncGenerator
import os
import logging

logger = logging.getLogger(__name__)

# Configuración de MongoDB
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "brainlens")

# Cliente asíncrono de MongoDB
async_client: AsyncIOMotorClient = None

# Cliente síncrono de MongoDB (para operaciones que requieran sincronía)
sync_client: MongoClient = None

async def connect_to_mongo():
    """Conectar a MongoDB"""
    global async_client, sync_client
    
    try:
        # Cliente asíncrono
        async_client = AsyncIOMotorClient(MONGODB_URL)
        
        # Cliente síncrono
        sync_client = MongoClient(MONGODB_URL)
        
        # Verificar conexión
        await async_client.admin.command('ping')
        logger.info("Conexión exitosa a MongoDB")
        
    except Exception as e:
        logger.error(f"Error conectando a MongoDB: {e}")
        raise

async def close_mongo_connection():
    """Cerrar conexión a MongoDB"""
    global async_client, sync_client
    
    if async_client:
        async_client.close()
    if sync_client:
        sync_client.close()
    logger.info("Conexión a MongoDB cerrada")

def get_database():
    """Obtener la base de datos"""
    if not async_client:
        raise Exception("MongoDB no está conectado")
    return async_client[DATABASE_NAME]

def get_sync_database():
    """Obtener la base de datos (versión síncrona)"""
    if not sync_client:
        raise Exception("MongoDB no está conectado")
    return sync_client[DATABASE_NAME]

async def get_db() -> AsyncGenerator:
    """Dependency para FastAPI"""
    db = get_database()
    try:
        yield db
    finally:
        # La conexión se mantiene abierta durante toda la aplicación
        pass

# Función para crear índices (equivalente a create_tables en SQL)
async def create_indexes():
    """Crear índices necesarios en las colecciones"""
    db = get_database()
    
    # Ejemplo de índices (ajustar según tus necesidades)
    # await db.users.create_index("email", unique=True)
    # await db.users.create_index("username", unique=True)
    
    logger.info("Índices de MongoDB creados")

# Función para verificar el estado de la base de datos
async def health_check():
    """Verificar el estado de la conexión a MongoDB"""
    try:
        await async_client.admin.command('ping')
        return {"status": "healthy", "database": "mongodb"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)} 