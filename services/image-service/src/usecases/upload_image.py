import os
import uuid
from datetime import datetime
from typing import Optional
import logging

from domain.entities.Image import Image as ImageEntity
from domain.repositories.ImageRepository import ImageRepository
from infrastructure.storage import StorageService
from tasks.tumor_analysis_tasks import analyze_tumor_task

logger = logging.getLogger(__name__)

class UploadImageUseCase:
    def __init__(self, image_repository: ImageRepository, storage_service: StorageService):
        self.image_repository = image_repository
        self.storage_service = storage_service
        logger.info(f"UploadImageUseCase inicializado con storage_service: {type(storage_service)}")
        
    async def execute(self, file_content: bytes, original_filename: str, user_id: str, custom_filename: Optional[str] = None) -> ImageEntity:
        """Subir una nueva imagen e iniciar procesamiento en background"""
        try:
            logger.info(f"Iniciando ejecución de upload_image para archivo: {original_filename}")
            
            # Validar archivo
            if not file_content:
                raise ValueError("El archivo está vacío")
            
            logger.info("Archivo validado - no está vacío")
            
            # Validar tipo de archivo
            logger.info(f"Validando tipo de archivo: {original_filename}")
            if not self.storage_service.is_valid_image_type(original_filename):
                raise ValueError("Tipo de archivo no válido")
            
            logger.info("Tipo de archivo validado")
            
            # Validar tamaño de archivo
            logger.info(f"Validando tamaño de archivo: {len(file_content)} bytes")
            if len(file_content) > self.storage_service.get_max_file_size():
                raise ValueError("El archivo es demasiado grande")
            
            logger.info("Tamaño de archivo validado")
            
            # Usar nombre personalizado si se proporciona
            final_filename = custom_filename if custom_filename else original_filename
            
            logger.info(f"Guardando imagen con storage_service: {type(self.storage_service)}")
            logger.info(f"Métodos disponibles: {dir(self.storage_service)}")
            
            # Guardar archivo en almacenamiento usando el método correcto
            unique_filename, file_info = await self.storage_service.save_image(file_content, original_filename, user_id)
            
            logger.info(f"Archivo guardado exitosamente: {unique_filename}")
            
            # Crear entidad de imagen con status "pending"
            image = ImageEntity(
                # No especificar id - se generará automáticamente
                filename=unique_filename,
                original_filename=final_filename,
                file_path=file_info["file_path"],
                file_size=file_info["file_size"],
                mime_type=file_info["mime_type"],
                width=file_info["width"],
                height=file_info["height"],
                user_id=user_id,
                upload_date=datetime.utcnow(),
                processing_status="pending",  # Estado inicial
                metadata={
                    "processing_started": datetime.utcnow().isoformat(),
                    "processing_status": "pending",
                    **file_info["metadata"]
                }
            )
            
            logger.info("Entidad de imagen creada")
            
            # Guardar en base de datos
            saved_image = await self.image_repository.save(image)
            
            logger.info(f"Imagen guardada en base de datos con ID: {saved_image.id}")
            
            # Iniciar procesamiento en background
            logger.info(f"Iniciando procesamiento en background para imagen: {saved_image.id}")
            analyze_tumor_task.delay(str(saved_image.id))
            
            return saved_image
            
        except Exception as e:
            logger.error(f"Error en upload_image: {str(e)}")
            logger.error(f"Tipo de error: {type(e)}")
            import traceback
            logger.error(f"Traceback completo: {traceback.format_exc()}")
            raise
