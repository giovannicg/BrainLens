from typing import Optional
from ...domain.entities.Image import Image
from ...domain.repositories.ImageRepository import ImageRepository
from ...infrastructure.storage import storage_service

class UploadImageUseCase:
    def __init__(self, image_repository: ImageRepository):
        self.image_repository = image_repository
    
    async def execute(self, file_content: bytes, original_filename: str, user_id: str) -> Optional[Image]:
        """Ejecutar el caso de uso de subir imagen"""
        try:
            # Validar tipo de archivo
            if not storage_service.is_valid_image_type(original_filename):
                raise ValueError("Tipo de archivo no válido")
            
            # Validar tamaño de archivo
            if len(file_content) > storage_service.get_max_file_size():
                raise ValueError("Archivo demasiado grande")
            
            # Guardar imagen en almacenamiento
            filename, file_info = await storage_service.save_image(
                file_content, original_filename, user_id
            )
            
            # Crear entidad Image
            image = Image(
                filename=filename,
                original_filename=original_filename,
                file_path=file_info["file_path"],
                file_size=file_info["file_size"],
                mime_type=file_info["mime_type"],
                width=file_info["width"],
                height=file_info["height"],
                user_id=user_id,
                processing_status="pending",
                metadata=file_info["metadata"]
            )
            
            # Guardar en base de datos
            saved_image = await self.image_repository.save(image)
            
            return saved_image
            
        except Exception as e:
            # Si hay error, limpiar archivo guardado
            if 'file_info' in locals():
                await storage_service.delete_image(file_info["file_path"])
            raise e
