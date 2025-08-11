from typing import List, Optional
from domain.entities.Annotation import Annotation
from domain.repositories.AnnotationRepository import AnnotationRepository

class GetAnnotationsUseCase:
    def __init__(self, annotation_repository: AnnotationRepository):
        self.annotation_repository = annotation_repository
    
    async def execute(self, user_id: str = None, image_id: str = None, 
                     skip: int = 0, limit: int = 100) -> List[Annotation]:
        """Ejecutar el caso de uso de obtener anotaciones"""
        if user_id:
            return await self.annotation_repository.find_by_user_id(user_id)
        elif image_id:
            return await self.annotation_repository.find_by_image_id(image_id)
        else:
            return await self.annotation_repository.find_all(skip=skip, limit=limit)

class GetAnnotationByIdUseCase:
    def __init__(self, annotation_repository: AnnotationRepository):
        self.annotation_repository = annotation_repository
    
    async def execute(self, annotation_id: str) -> Annotation:
        """Ejecutar el caso de uso de obtener anotación por ID"""
        annotation = await self.annotation_repository.find_by_id(annotation_id)
        if not annotation:
            raise ValueError("Anotación no encontrada")
        return annotation

class GetAnnotationsByStatusUseCase:
    def __init__(self, annotation_repository: AnnotationRepository):
        self.annotation_repository = annotation_repository
    
    async def execute(self, status: str) -> List[Annotation]:
        """Ejecutar el caso de uso de obtener anotaciones por estado"""
        return await self.annotation_repository.find_by_status(status)

class GetAnnotationsByCategoryUseCase:
    def __init__(self, annotation_repository: AnnotationRepository):
        self.annotation_repository = annotation_repository
    
    async def execute(self, category: str) -> List[Annotation]:
        """Ejecutar el caso de uso de obtener anotaciones por categoría"""
        return await self.annotation_repository.find_by_category(category)

class GetPendingReviewsUseCase:
    def __init__(self, annotation_repository: AnnotationRepository):
        self.annotation_repository = annotation_repository
    
    async def execute(self) -> List[Annotation]:
        """Ejecutar el caso de uso de obtener anotaciones pendientes de revisión"""
        return await self.annotation_repository.find_pending_reviews()
