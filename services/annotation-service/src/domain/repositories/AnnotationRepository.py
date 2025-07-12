from abc import ABC, abstractmethod
from typing import List, Optional
from ..entities.Annotation import Annotation

class AnnotationRepository(ABC):
    @abstractmethod
    async def save(self, annotation: Annotation) -> Annotation:
        """Guardar una anotación en el repositorio"""
        pass
    
    @abstractmethod
    async def find_by_id(self, annotation_id: str) -> Optional[Annotation]:
        """Buscar una anotación por su ID"""
        pass
    
    @abstractmethod
    async def find_by_image_id(self, image_id: str) -> List[Annotation]:
        """Buscar todas las anotaciones de una imagen"""
        pass
    
    @abstractmethod
    async def find_by_user_id(self, user_id: str) -> List[Annotation]:
        """Buscar todas las anotaciones de un usuario"""
        pass
    
    @abstractmethod
    async def find_by_status(self, status: str) -> List[Annotation]:
        """Buscar anotaciones por estado"""
        pass
    
    @abstractmethod
    async def find_by_category(self, category: str) -> List[Annotation]:
        """Buscar anotaciones por categoría"""
        pass
    
    @abstractmethod
    async def find_all(self, skip: int = 0, limit: int = 100) -> List[Annotation]:
        """Obtener todas las anotaciones con paginación"""
        pass
    
    @abstractmethod
    async def update(self, annotation_id: str, annotation_data: dict) -> Optional[Annotation]:
        """Actualizar una anotación"""
        pass
    
    @abstractmethod
    async def delete(self, annotation_id: str) -> bool:
        """Eliminar una anotación"""
        pass
    
    @abstractmethod
    async def count_by_image_id(self, image_id: str) -> int:
        """Contar anotaciones de una imagen"""
        pass
    
    @abstractmethod
    async def find_pending_reviews(self) -> List[Annotation]:
        """Buscar anotaciones pendientes de revisión"""
        pass
