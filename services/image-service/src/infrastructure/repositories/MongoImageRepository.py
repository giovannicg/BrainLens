from typing import List, Optional
from bson import ObjectId
from domain.entities.Image import Image
from domain.repositories.ImageRepository import ImageRepository
from infrastructure.database import database

class MongoImageRepository(ImageRepository):
    def __init__(self):
        self.collection = database.get_collection("images")
    
    async def save(self, image: Image) -> Image:
        """Guardar una imagen en MongoDB"""
        image_dict = image.model_dump(by_alias=True)
        if image_dict.get("_id") is None:
            image_dict["_id"] = ObjectId()
        
        result = await self.collection.insert_one(image_dict)
        # Convertir ObjectId a string
        image.id = str(result.inserted_id)
        return image
    
    async def find_by_id(self, image_id: str) -> Optional[Image]:
        """Buscar una imagen por su ID"""
        try:
            doc = await self.collection.find_one({"_id": ObjectId(image_id)})
            if doc:
                # Convertir ObjectId a string
                doc["_id"] = str(doc["_id"])
                return Image.model_validate(doc)
            return None
        except Exception:
            return None
    
    async def find_by_user_id(self, user_id: str) -> List[Image]:
        """Buscar todas las imágenes de un usuario"""
        cursor = self.collection.find({"user_id": user_id})
        images = []
        async for doc in cursor:
            # Convertir ObjectId a string
            doc["_id"] = str(doc["_id"])
            images.append(Image.model_validate(doc))
        return images
    
    async def find_all(self, skip: int = 0, limit: int = 100) -> List[Image]:
        """Obtener todas las imágenes con paginación"""
        cursor = self.collection.find().skip(skip).limit(limit)
        images = []
        async for doc in cursor:
            # Convertir ObjectId a string
            doc["_id"] = str(doc["_id"])
            images.append(Image.model_validate(doc))
        return images
    
    async def update(self, image_id: str, image_data: dict) -> Optional[Image]:
        """Actualizar una imagen"""
        try:
            result = await self.collection.update_one(
                {"_id": ObjectId(image_id)},
                {"$set": image_data}
            )
            if result.modified_count > 0:
                return await self.find_by_id(image_id)
            return None
        except Exception:
            return None
    
    async def delete(self, image_id: str) -> bool:
        """Eliminar una imagen"""
        try:
            result = await self.collection.delete_one({"_id": ObjectId(image_id)})
            return result.deleted_count > 0
        except Exception:
            return False
    
    async def find_by_status(self, status: str) -> List[Image]:
        """Buscar imágenes por estado de procesamiento"""
        cursor = self.collection.find({"processing_status": status})
        images = []
        async for doc in cursor:
            # Convertir ObjectId a string
            doc["_id"] = str(doc["_id"])
            images.append(Image.model_validate(doc))
        return images 