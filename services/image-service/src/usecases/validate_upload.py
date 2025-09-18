import os
import logging
from datetime import datetime
from typing import Optional, Dict, Any
import mimetypes

from infrastructure.storage import StorageService
from infrastructure.repositories.MongoImageRepository import MongoImageRepository
from domain.entities.Image import Image as ImageEntity
import os
import requests

logger = logging.getLogger(__name__)

class ValidateUploadUseCase:
    def __init__(self, storage_service: StorageService, image_repository: MongoImageRepository):
        self.storage_service = storage_service
        self.image_repository = image_repository
        logger.info(f"ValidateUploadUseCase inicializado (sin Celery) con storage_service: {type(storage_service)}")
        
    async def execute(self, file_content: bytes, original_filename: str, user_id: str, custom_filename: Optional[str] = None) -> Dict[str, Any]:
        """Validar y guardar la imagen de forma síncrona y devolver la entidad creada."""
        try:
            logger.info(f"[VALIDATE_UPLOAD] Inicio para archivo: {original_filename}")

            # Validaciones básicas
            if not file_content:
                raise ValueError("El archivo está vacío")
            if not self.storage_service.is_valid_image_type(original_filename):
                raise ValueError("Tipo de archivo no válido")
            if len(file_content) > self.storage_service.get_max_file_size():
                raise ValueError("El archivo es demasiado grande")

            # Determinar MIME
            mime_type, _ = mimetypes.guess_type(original_filename)
            if not mime_type:
                mime_type = "application/octet-stream"

            # Validación médica directa
            from infrastructure.medical_image_validator import MedicalImageValidator
            validator = MedicalImageValidator()
            try:
                is_valid_ct, validation_info = await validator.validate_brain_ct(file_content, mime_type)
            except Exception as val_err:
                return {
                    "image": None,
                    "message": "Error en validación médica",
                    "error_code": "validator_error",
                    "error_detail": str(val_err),
                }

            if not is_valid_ct:
                return {
                    "image": None,
                    "message": f"La imagen no es una tomografía cerebral válida. {validation_info.get('descripcion', '')}",
                    "error_code": "invalid_medical_image",
                    "error_detail": validation_info.get('descripcion', ''),
                }

            # Guardar en almacenamiento definitivo
            unique_filename, file_info = await self.storage_service.save_image(file_content, original_filename, user_id)

            # Crear y persistir entidad
            image = ImageEntity(
                filename=unique_filename,
                original_filename=custom_filename if custom_filename else original_filename,
                file_path=file_info["file_path"],
                file_size=file_info["file_size"],
                mime_type=file_info["mime_type"],
                width=file_info["width"],
                height=file_info["height"],
                user_id=user_id,
                upload_date=datetime.utcnow(),
                processing_status="pending",
                metadata={
                    "medical_validation": {
                        "status": "completed",
                        "is_valid_ct": True,
                        "descripcion": validation_info.get("descripcion", "Validación médica exitosa"),
                        "completed_at": datetime.utcnow().isoformat(),
                    },
                    **file_info.get("metadata", {}),
                },
            )

            saved = await self.image_repository.save(image)

            # Predicción síncrona (colab-service)
            prediction_url = os.getenv("COLAB_PREDICT_URL", "http://colab-service:8004/predict")
            try:
                # Usar el contenido de la imagen que ya tenemos en memoria
                files = {"image": (original_filename, file_content, mime_type)}
                resp = requests.post(prediction_url, files=files, timeout=300)
                if resp.status_code == 200:
                    pred_data = resp.json()
                    # Actualizar imagen a completed con predicción
                    update_data: Dict[str, Any] = {
                        "processing_status": "completed",
                        "metadata.prediction": pred_data,
                        "metadata.processing_started": image.metadata.get("processing_started") if image.metadata else datetime.utcnow().isoformat(),
                        "metadata.processing_completed": datetime.utcnow().isoformat(),
                        "metadata.processing_status": "completed",
                    }
                    await self.image_repository.update(str(saved.id), update_data)
                    # Traer entidad actualizada
                    saved = await self.image_repository.find_by_id(str(saved.id))
                else:
                    return {
                        "image": saved,
                        "message": "Error durante la predicción",
                        "error_code": "prediction_error",
                        "error_detail": resp.text,
                    }
            except Exception as pred_err:
                return {
                    "image": saved,
                    "message": "Excepción durante la predicción",
                    "error_code": "prediction_exception",
                    "error_detail": str(pred_err),
                }

            return {
                "image": saved,
                "message": "Imagen validada, guardada y predicción generada",
            }

        except Exception as e:
            logger.error(f"Error en validate_upload síncrono: {str(e)}")
            raise
