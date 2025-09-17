from abc import ABC, abstractmethod
from typing import List, Optional
from ..entities.Image import Image

class ImageRepository(ABC):
    @abstractmethod
    async def save(self, image: Image) -> Image:
        """Guardar una imagen en el repositorio"""
        pass
    
    @abstractmethod
    async def find_by_id(self, image_id: str) -> Optional[Image]:
        """Buscar una imagen por su ID"""
        pass
    
    @abstractmethod
    async def find_by_user_id(self, user_id: str) -> List[Image]:
        """Buscar todas las imágenes de un usuario"""
        pass
    
    @abstractmethod
    async def find_all(self, skip: int = 0, limit: int = 100) -> List[Image]:
        """Obtener todas las imágenes con paginación"""
        pass
    
    @abstractmethod
    async def update(self, image_id: str, image_data: dict) -> Optional[Image]:
        """Actualizar una imagen"""
        pass
    
    @abstractmethod
    async def delete(self, image_id: str) -> bool:
        """Eliminar una imagen"""
        pass
    
    @abstractmethod
    async def find_by_status(self, status: str) -> List[Image]:
        """Buscar imágenes por estado de procesamiento"""
        pass
