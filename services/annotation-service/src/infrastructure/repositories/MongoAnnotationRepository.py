from typing import List, Optional
from bson import ObjectId
from ...domain.entities.Annotation import Annotation
from ...domain.repositories.AnnotationRepository import AnnotationRepository
from ..database import database
from datetime import datetime

class MongoAnnotationRepository(AnnotationRepository):
    def __init__(self):
        self.collection = database.get_collection("annotations")
    
    async def save(self, annotation: Annotation) -> Annotation:
        """Guardar una anotación en MongoDB"""
        annotation_dict = annotation.dict(by_alias=True)
        if annotation_dict.get("_id") is None:
            annotation_dict["_id"] = ObjectId()
        
        result = await self.collection.insert_one(annotation_dict)
        annotation.id = result.inserted_id
        return annotation
    
    async def find_by_id(self, annotation_id: str) -> Optional[Annotation]:
        """Buscar una anotación por su ID"""
        try:
            doc = await self.collection.find_one({"_id": ObjectId(annotation_id)})
            if doc:
                return Annotation(**doc)
            return None
        except Exception:
            return None
    
    async def find_by_image_id(self, image_id: str) -> List[Annotation]:
        """Buscar todas las anotaciones de una imagen"""
        cursor = self.collection.find({"image_id": image_id})
        annotations = []
        async for doc in cursor:
            annotations.append(Annotation(**doc))
        return annotations
    
    async def find_by_user_id(self, user_id: str) -> List[Annotation]:
        """Buscar todas las anotaciones de un usuario"""
        cursor = self.collection.find({"user_id": user_id})
        annotations = []
        async for doc in cursor:
            annotations.append(Annotation(**doc))
        return annotations
    
    async def find_by_status(self, status: str) -> List[Annotation]:
        """Buscar anotaciones por estado"""
        cursor = self.collection.find({"status": status})
        annotations = []
        async for doc in cursor:
            annotations.append(Annotation(**doc))
        return annotations
    
    async def find_by_category(self, category: str) -> List[Annotation]:
        """Buscar anotaciones por categoría"""
        cursor = self.collection.find({"category": category})
        annotations = []
        async for doc in cursor:
            annotations.append(Annotation(**doc))
        return annotations
    
    async def find_all(self, skip: int = 0, limit: int = 100) -> List[Annotation]:
        """Obtener todas las anotaciones con paginación"""
        cursor = self.collection.find().skip(skip).limit(limit)
        annotations = []
        async for doc in cursor:
            annotations.append(Annotation(**doc))
        return annotations
    
    async def update(self, annotation_id: str, annotation_data: dict) -> Optional[Annotation]:
        """Actualizar una anotación"""
        try:
            # Añadir timestamp de actualización
            annotation_data["updated_at"] = datetime.utcnow()
            
            result = await self.collection.update_one(
                {"_id": ObjectId(annotation_id)},
                {"$set": annotation_data}
            )
            if result.modified_count > 0:
                return await self.find_by_id(annotation_id)
            return None
        except Exception:
            return None
    
    async def delete(self, annotation_id: str) -> bool:
        """Eliminar una anotación"""
        try:
            result = await self.collection.delete_one({"_id": ObjectId(annotation_id)})
            return result.deleted_count > 0
        except Exception:
            return False
    
    async def count_by_image_id(self, image_id: str) -> int:
        """Contar anotaciones de una imagen"""
        try:
            count = await self.collection.count_documents({"image_id": image_id})
            return count
        except Exception:
            return 0
    
    async def find_pending_reviews(self) -> List[Annotation]:
        """Buscar anotaciones pendientes de revisión"""
        cursor = self.collection.find({"status": "pending"})
        annotations = []
        async for doc in cursor:
            annotations.append(Annotation(**doc))
        return annotations 