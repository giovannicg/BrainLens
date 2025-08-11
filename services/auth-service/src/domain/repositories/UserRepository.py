from abc import ABC, abstractmethod
from typing import Optional, List
from ..entities.User import User

class UserRepository(ABC):
    """Interfaz del repositorio de usuarios"""
    
    @abstractmethod
    async def create(self, user: User) -> User:
        """Crea un nuevo usuario"""
        pass
    
    @abstractmethod
    async def get_by_id(self, user_id: str) -> Optional[User]:
        """Obtiene un usuario por su ID"""
        pass
    
    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[User]:
        """Obtiene un usuario por su email"""
        pass
    
    @abstractmethod
    async def get_by_username(self, username: str) -> Optional[User]:
        """Obtiene un usuario por su username"""
        pass
    
    @abstractmethod
    async def update(self, user: User) -> User:
        """Actualiza un usuario existente"""
        pass
    
    @abstractmethod
    async def delete(self, user_id: str) -> bool:
        """Elimina un usuario por su ID"""
        pass
    
    @abstractmethod
    async def list_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Lista usuarios con paginación"""
        pass
    
    @abstractmethod
    async def update_last_login(self, user_id: str) -> bool:
        """Actualiza la fecha del último login"""
        pass
    
    @abstractmethod
    async def verify_user(self, user_id: str) -> bool:
        """Marca un usuario como verificado"""
        pass
    
    @abstractmethod
    async def deactivate_user(self, user_id: str) -> bool:
        """Desactiva un usuario"""
        pass
