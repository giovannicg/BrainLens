import os
from datetime import datetime
from typing import Optional, Dict, Any
import logging

from infrastructure.storage import StorageService
from infrastructure.repositories.MongoImageRepository import MongoImageRepository
from domain.entities.Image import Image as ImageEntity

logger = logging.getLogger(__name__)

class UploadImageUseCase:
    def __init__(self, image_repository: MongoImageRepository, storage_service: StorageService):
        self.image_repository = image_repository
        self.storage_service = storage_service
        logger.info(f"UploadImageUseCase inicializado (sin Celery) con storage_service: {type(storage_service)}")
        
    async def execute(self, file_content: bytes, original_filename: str, user_id: str, custom_filename: Optional[str] = None) -> Dict[str, Any]:
        """Subir una nueva imagen de forma síncrona y guardarla."""
        try:
            logger.info(f"[UPLOAD_UC] Inicio para archivo: {original_filename}")

            # Validaciones básicas
            if not file_content:
                raise ValueError("El archivo está vacío")
            if not self.storage_service.is_valid_image_type(original_filename):
                raise ValueError("Tipo de archivo no válido")
            if len(file_content) > self.storage_service.get_max_file_size():
                raise ValueError("El archivo es demasiado grande")

            # Guardar a almacenamiento definitivo
            unique_filename, file_info = await self.storage_service.save_image(file_content, original_filename, user_id)

            # Crear entidad
            image = ImageEntity(
                filename=unique_filename,
                original_filename=custom_filename if custom_filename else original_filename,
                file_path=file_info["file_path"],
                file_size=file_info["file_size"],
                mime_type=file_info["mime_type"],
                width=file_info.get("width"),
                height=file_info.get("height"),
                user_id=user_id,
                upload_date=datetime.utcnow(),
                processing_status="pending",
                metadata={**file_info.get("metadata", {})},
            )

            saved = await self.image_repository.save(image)
            return {"image": saved, "message": "Imagen subida correctamente"}

        except Exception as e:
            logger.error(f"Error en upload_image síncrono: {str(e)}")
            raise

