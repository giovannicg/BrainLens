from typing import List, Optional
from domain.entities.Annotation import Annotation
from domain.repositories.AnnotationRepository import AnnotationRepository
from infrastructure.repositories.MongoAnnotationRepository import MongoAnnotationRepository

class AnnotationGateway(AnnotationRepository):
    """Gateway para las anotaciones que conecta los adapters con la infraestructura"""
    
    def __init__(self):
        self.repository: AnnotationRepository = MongoAnnotationRepository()
    
    async def save(self, annotation: Annotation) -> Annotation:
        """Guarda una nueva anotación"""
        return await self.repository.save(annotation)
    
    async def find_by_id(self, annotation_id: str) -> Optional[Annotation]:
        """Busca una anotación por su ID"""
        return await self.repository.find_by_id(annotation_id)
    
    async def find_all(self, skip: int = 0, limit: int = 100) -> List[Annotation]:
        """Obtiene todas las anotaciones con paginación"""
        return await self.repository.find_all(skip, limit)
    
    async def find_by_image_id(self, image_id: str) -> List[Annotation]:
        """Busca anotaciones por ID de imagen"""
        return await self.repository.find_by_image_id(image_id)
    
    async def find_by_user_id(self, user_id: str) -> List[Annotation]:
        """Busca anotaciones por ID de usuario"""
        return await self.repository.find_by_user_id(user_id)
    
    async def find_by_status(self, status: str) -> List[Annotation]:
        """Busca anotaciones por estado"""
        return await self.repository.find_by_status(status)
    
    async def find_by_category(self, category: str) -> List[Annotation]:
        """Busca anotaciones por categoría"""
        return await self.repository.find_by_category(category)
    
    async def find_pending_reviews(self) -> List[Annotation]:
        """Busca anotaciones pendientes de revisión"""
        return await self.repository.find_pending_reviews()
    
    async def update(self, annotation_id: str, annotation_data: dict) -> Optional[Annotation]:
        """Actualiza una anotación"""
        return await self.repository.update(annotation_id, annotation_data)
    
    async def delete(self, annotation_id: str) -> bool:
        """Elimina una anotación"""
        return await self.repository.delete(annotation_id)
    
    async def count_by_image_id(self, image_id: str) -> int:
        """Cuenta anotaciones de una imagen"""
        return await self.repository.count_by_image_id(image_id)
