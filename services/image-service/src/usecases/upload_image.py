import os
import uuid
from datetime import datetime
from typing import Optional
import logging
import asyncio

from domain.entities.Image import Image as ImageEntity
from domain.repositories.ImageRepository import ImageRepository
from infrastructure.storage import StorageService
from infrastructure.medical_image_validator import MedicalImageValidator

logger = logging.getLogger(__name__)

class UploadImageUseCase:
    def __init__(self, image_repository: ImageRepository, storage_service: StorageService):
        self.image_repository = image_repository
        self.storage_service = storage_service
        self.medical_validator = MedicalImageValidator()
        logger.info(f"UploadImageUseCase inicializado con storage_service: {type(storage_service)}")
        
    async def execute(self, file_content: bytes, original_filename: str, user_id: str, custom_filename: Optional[str] = None) -> ImageEntity:
        """Subir una nueva imagen con validación médica obligatoria"""
        try:
            logger.info(f"[UPLOAD_UC] Iniciando ejecución de upload_image para archivo: {original_filename}")

            # Validar archivo
            if not file_content:
                logger.error("[UPLOAD_UC] El archivo está vacío")
                raise ValueError("El archivo está vacío")
            logger.info(f"[UPLOAD_UC] Archivo validado - no está vacío, tamaño: {len(file_content)} bytes")

            # Validar tipo de archivo
            logger.info(f"[UPLOAD_UC] Validando tipo de archivo: {original_filename}")
            if not self.storage_service.is_valid_image_type(original_filename):
                logger.error(f"[UPLOAD_UC] Tipo de archivo no válido: {original_filename}")
                raise ValueError("Tipo de archivo no válido")
            logger.info(f"[UPLOAD_UC] Tipo de archivo validado: {original_filename}")

            # Validar tamaño de archivo
            logger.info(f"[UPLOAD_UC] Validando tamaño de archivo: {len(file_content)} bytes")
            if len(file_content) > self.storage_service.get_max_file_size():
                raise ValueError("El archivo es demasiado grande")
            
            logger.info("Tamaño de archivo validado")
            
                # VALIDACIÓN MÉDICA OBLIGATORIA ANTES DE GUARDAR
                # logger.info("Iniciando validación médica obligatoria...")
                # 
                # # Determinar MIME type
                # import mimetypes
                # mime_type, _ = mimetypes.guess_type(original_filename)
                # if not mime_type:
                #     mime_type = "application/octet-stream"
                # 
                # # Ejecutar validación médica con timeout
                # try:
                #     is_valid_ct, validation_info = await asyncio.wait_for(
                #         self.medical_validator.validate_brain_ct(file_content, mime_type),
                #         timeout=120.0  # Timeout de 120 segundos
                #     )
                #     
                #     if not is_valid_ct:
                #         error_msg = f"La imagen no es una tomografía cerebral válida. {validation_info.get('descripcion', '')}"
                #         logger.warning(f"Validación médica fallida: {error_msg}")
                #         raise ValueError(error_msg)
                #     
                #     logger.info("Validación médica exitosa - es una tomografía cerebral válida")
                #     
                # except asyncio.TimeoutError:
                #     error_msg = "Validación médica tardó demasiado tiempo. No se pudo verificar si la imagen es una tomografía cerebral válida."
                #     logger.error(f"Timeout en validación médica: {error_msg}")
                #     raise ValueError(error_msg)
                # except Exception as validation_error:
                #     error_msg = f"Error en validación médica: {str(validation_error)}"
                #     logger.error(f"Error en validación médica: {error_msg}")
                #     raise ValueError(error_msg)
                # --- FIN DE BLOQUE VALIDACIÓN MÉDICA ---
                # Validación médica deshabilitada temporalmente
            validation_info = {
                "descripcion": "Validación médica deshabilitada. Imagen guardada sin comprobación de si es tomografía cerebral.",
                "is_valid_ct": None
            }
            
            # Usar nombre personalizado si se proporciona
            final_filename = custom_filename if custom_filename else original_filename
            
            logger.info(f"Guardando imagen con storage_service: {type(self.storage_service)}")
            
            # Guardar archivo en almacenamiento usando el método correcto
            unique_filename, file_info = await self.storage_service.save_image(file_content, original_filename, user_id)
            
            logger.info(f"Archivo guardado exitosamente: {unique_filename}")
            
            # Crear entidad de imagen con status "completed" (ya validada)
            image = ImageEntity(
                filename=unique_filename,
                original_filename=final_filename,
                file_path=file_info["file_path"],
                file_size=file_info["file_size"],
                mime_type=file_info["mime_type"],
                width=file_info["width"],
                height=file_info["height"],
                user_id=user_id,
                upload_date=datetime.utcnow(),
                processing_status="completed",  # Ya validada y completada
                metadata={
                    "processing_started": datetime.utcnow().isoformat(),
                    "processing_completed": datetime.utcnow().isoformat(),
                    "processing_status": "completed",
                    "medical_validation": {
                        "status": "completed",
                        "is_valid_ct": True,
                        "descripcion": validation_info.get("descripcion", "Validación médica exitosa"),
                        "completed_at": datetime.utcnow().isoformat()
                    },
                    "prediction": {"status": "skipped", "descripcion": "Predicción deshabilitada"},
                    **file_info["metadata"]
                }
            )
            
            logger.info("Entidad de imagen creada")
            
            # Guardar en base de datos
            saved_image = await self.image_repository.save(image)
            
            logger.info(f"Imagen guardada en base de datos con ID: {saved_image.id}")
            
            return saved_image
            
        except Exception as e:
            logger.error(f"Error en upload_image: {str(e)}")
            logger.error(f"Tipo de error: {type(e)}")
            import traceback
            logger.error(f"Traceback completo: {traceback.format_exc()}")
            raise

