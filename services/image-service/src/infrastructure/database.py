import os
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

class Database:
    client: AsyncIOMotorClient = None
    
    @classmethod
    async def connect_db(cls):
        """Conectar a la base de datos MongoDB"""
        mongodb_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
        database_name = os.getenv("DATABASE_NAME", "brainlens")
        
        cls.client = AsyncIOMotorClient(mongodb_url)
        cls.database = cls.client[database_name]
        
        print(f"Conectado a MongoDB: {database_name}")
    
    @classmethod
    async def close_db(cls):
        """Cerrar conexión a la base de datos"""
        if cls.client:
            cls.client.close()
            print("Conexión a MongoDB cerrada")
    
    @classmethod
    def get_collection(cls, collection_name: str):
        """Obtener una colección de MongoDB"""
        return cls.database[collection_name]

# Instancia global de la base de datos
database = Database() 