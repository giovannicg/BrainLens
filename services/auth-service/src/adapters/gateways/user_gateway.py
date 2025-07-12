from typing import Optional, List
from datetime import datetime
from bson import ObjectId
from ...domain.entities.User import User
from ...domain.repositories.UserRepository import UserRepository
from ...infrastructure.database import get_database
import logging

logger = logging.getLogger(__name__)

class UserGateway(UserRepository):
    """Implementación del repositorio de usuarios con MongoDB"""
    
    def __init__(self):
        self.db = get_database()
        self.collection = self.db.users
    
    async def create(self, user: User) -> User:
        """Crea un nuevo usuario"""
        try:
            user_dict = user.to_dict()
            user_dict['created_at'] = datetime.utcnow()
            user_dict['updated_at'] = datetime.utcnow()
            
            result = await self.collection.insert_one(user_dict)
            user.id = str(result.inserted_id)
            
            logger.info(f"Usuario creado: {user.email}")
            return user
            
        except Exception as e:
            logger.error(f"Error creando usuario: {e}")
            raise
    
    async def get_by_id(self, user_id: str) -> Optional[User]:
        """Obtiene un usuario por su ID"""
        try:
            user_data = await self.collection.find_one({"_id": ObjectId(user_id)})
            if user_data:
                return User.from_dict(user_data)
            return None
            
        except Exception as e:
            logger.error(f"Error obteniendo usuario por ID: {e}")
            return None
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Obtiene un usuario por su email"""
        try:
            user_data = await self.collection.find_one({"email": email})
            if user_data:
                return User.from_dict(user_data)
            return None
            
        except Exception as e:
            logger.error(f"Error obteniendo usuario por email: {e}")
            return None
    
    async def get_by_username(self, username: str) -> Optional[User]:
        """Obtiene un usuario por su username"""
        try:
            user_data = await self.collection.find_one({"username": username})
            if user_data:
                return User.from_dict(user_data)
            return None
            
        except Exception as e:
            logger.error(f"Error obteniendo usuario por username: {e}")
            return None
    
    async def update(self, user: User) -> User:
        """Actualiza un usuario existente"""
        try:
            user_dict = user.to_dict()
            user_dict['updated_at'] = datetime.utcnow()
            
            await self.collection.update_one(
                {"_id": ObjectId(user.id)},
                {"$set": user_dict}
            )
            
            logger.info(f"Usuario actualizado: {user.email}")
            return user
            
        except Exception as e:
            logger.error(f"Error actualizando usuario: {e}")
            raise
    
    async def delete(self, user_id: str) -> bool:
        """Elimina un usuario por su ID"""
        try:
            result = await self.collection.delete_one({"_id": ObjectId(user_id)})
            if result.deleted_count > 0:
                logger.info(f"Usuario eliminado: {user_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error eliminando usuario: {e}")
            return False
    
    async def list_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Lista usuarios con paginación"""
        try:
            cursor = self.collection.find().skip(skip).limit(limit)
            users = []
            async for user_data in cursor:
                users.append(User.from_dict(user_data))
            return users
            
        except Exception as e:
            logger.error(f"Error listando usuarios: {e}")
            return []
    
    async def update_last_login(self, user_id: str) -> bool:
        """Actualiza la fecha del último login"""
        try:
            result = await self.collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": {"last_login": datetime.utcnow()}}
            )
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Error actualizando último login: {e}")
            return False
    
    async def verify_user(self, user_id: str) -> bool:
        """Marca un usuario como verificado"""
        try:
            result = await self.collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": {"is_verified": True, "updated_at": datetime.utcnow()}}
            )
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Error verificando usuario: {e}")
            return False
    
    async def deactivate_user(self, user_id: str) -> bool:
        """Desactiva un usuario"""
        try:
            result = await self.collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
            )
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Error desactivando usuario: {e}")
            return False
