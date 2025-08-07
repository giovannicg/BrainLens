from typing import List, Optional
from bson import ObjectId
from domain.entities.Annotation import Annotation
from domain.repositories.AnnotationRepository import AnnotationRepository
from ..database import database
from datetime import datetime

class MongoAnnotationRepository(AnnotationRepository):
    def __init__(self):
        self.collection = database.get_collection("annotations")

    def _doc_to_entity(self, doc) -> Annotation:
        print(f"DEBUG: _doc_to_entity called with doc: {doc}")
        # Convertir el _id a string para que Pydantic pueda manejarlo correctamente
        import logging
        logging.info(f"Converting doc: {doc}")
        if "_id" in doc:
            logging.info(f"Converting _id from {type(doc['_id'])} to string")
            doc["_id"] = str(doc["_id"])
            logging.info(f"Converted _id: {doc['_id']}")
        try:
            result = Annotation.model_validate(doc)
            logging.info(f"Successfully converted to Annotation: {result.id}")
            return result
        except Exception as e:
            logging.error(f"Error converting doc to Annotation: {e}")
            logging.error(f"Doc content: {doc}")
            raise

    async def save(self, annotation: Annotation) -> Annotation:
        """Guardar una anotación en MongoDB"""
        annotation_dict = annotation.model_dump(by_alias=True)
        if annotation_dict.get("_id") is None:
            annotation_dict["_id"] = ObjectId()
        try:
            result = await self.collection.insert_one(annotation_dict)
            annotation.id = result.inserted_id
            return annotation
        except Exception as e:
            import logging
            logging.error(f"Error al guardar anotación: {e}")
            raise
    
    async def find_by_id(self, annotation_id: str) -> Optional[Annotation]:
        """Buscar una anotación por su ID"""
        try:
            doc = await self.collection.find_one({"_id": ObjectId(annotation_id)})
            if doc:
                return self._doc_to_entity(doc)
            return None
        except Exception as e:
            import logging
            logging.error(f"Error al buscar anotación por ID: {e}")
            return None
    
    async def find_by_image_id(self, image_id: str) -> List[Annotation]:
        """Buscar todas las anotaciones de una imagen"""
        cursor = self.collection.find({"image_id": image_id})
        annotations = []
        async for doc in cursor:
            annotations.append(self._doc_to_entity(doc))
        return annotations
    
    async def find_by_user_id(self, user_id: str) -> List[Annotation]:
        """Buscar todas las anotaciones de un usuario"""
        cursor = self.collection.find({"user_id": user_id})
        annotations = []
        async for doc in cursor:
            annotations.append(self._doc_to_entity(doc))
        return annotations
    
    async def find_by_status(self, status: str) -> List[Annotation]:
        """Buscar anotaciones por estado"""
        cursor = self.collection.find({"status": status})
        annotations = []
        async for doc in cursor:
            annotations.append(self._doc_to_entity(doc))
        return annotations
    
    async def find_by_category(self, category: str) -> List[Annotation]:
        """Buscar anotaciones por categoría"""
        cursor = self.collection.find({"category": category})
        annotations = []
        async for doc in cursor:
            annotations.append(self._doc_to_entity(doc))
        return annotations
    
    async def find_all(self, skip: int = 0, limit: int = 100) -> List[Annotation]:
        """Obtener todas las anotaciones con paginación"""
        cursor = self.collection.find().skip(skip).limit(limit)
        annotations = []
        async for doc in cursor:
            annotations.append(self._doc_to_entity(doc))
        return annotations
    
    async def update(self, annotation_id: str, annotation_data: dict) -> Optional[Annotation]:
        """Actualizar una anotación"""
        try:
            annotation_data["updated_at"] = datetime.utcnow()
            result = await self.collection.update_one(
                {"_id": ObjectId(annotation_id)},
                {"$set": annotation_data}
            )
            if result.modified_count > 0:
                return await self.find_by_id(annotation_id)
            return None
        except Exception as e:
            import logging
            logging.error(f"Error al actualizar anotación: {e}")
            return None
    
    async def delete(self, annotation_id: str) -> bool:
        """Eliminar una anotación"""
        try:
            result = await self.collection.delete_one({"_id": ObjectId(annotation_id)})
            return result.deleted_count > 0
        except Exception as e:
            import logging
            logging.error(f"Error al eliminar anotación: {e}")
            return False
    
    async def count_by_image_id(self, image_id: str) -> int:
        """Contar anotaciones de una imagen"""
        try:
            count = await self.collection.count_documents({"image_id": image_id})
            return count
        except Exception as e:
            import logging
            logging.error(f"Error al contar anotaciones: {e}")
            return 0
    
    async def find_pending_reviews(self) -> List[Annotation]:
        """Buscar anotaciones pendientes de revisión"""
        cursor = self.collection.find({"status": "pending"})
        annotations = []
        async for doc in cursor:
            annotations.append(self._doc_to_entity(doc))
        return annotations