from ...domain.repositories.ImageRepository import ImageRepository
from ...infrastructure.storage import storage_service

class DeleteImageUseCase:
    def __init__(self, image_repository: ImageRepository):
        self.image_repository = image_repository
    
    async def execute(self, image_id: str) -> bool:
        """Ejecutar el caso de uso de eliminar imagen"""
        # Obtener la imagen primero
        image = await self.image_repository.find_by_id(image_id)
        if not image:
            raise ValueError("Imagen no encontrada")
        
        # Eliminar archivo del almacenamiento
        file_deleted = await storage_service.delete_image(image.file_path)
        
        # Eliminar registro de la base de datos
        db_deleted = await self.image_repository.delete(image_id)
        
        return file_deleted and db_deleted 