from typing import List
from ...domain.entities.Image import Image
from ...domain.repositories.ImageRepository import ImageRepository

class GetImagesUseCase:
    def __init__(self, image_repository: ImageRepository):
        self.image_repository = image_repository
    
    async def execute(self, user_id: str = None, skip: int = 0, limit: int = 100) -> List[Image]:
        """Ejecutar el caso de uso de obtener imágenes"""
        if user_id:
            return await self.image_repository.find_by_user_id(user_id)
        else:
            return await self.image_repository.find_all(skip=skip, limit=limit)

class GetImageByIdUseCase:
    def __init__(self, image_repository: ImageRepository):
        self.image_repository = image_repository
    
    async def execute(self, image_id: str) -> Image:
        """Ejecutar el caso de uso de obtener imagen por ID"""
        image = await self.image_repository.find_by_id(image_id)
        if not image:
            raise ValueError("Imagen no encontrada")
        return image

class GetImagesByStatusUseCase:
    def __init__(self, image_repository: ImageRepository):
        self.image_repository = image_repository
    
    async def execute(self, status: str) -> List[Image]:
        """Ejecutar el caso de uso de obtener imágenes por estado"""
        return await self.image_repository.find_by_status(status) 