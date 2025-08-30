import asyncio
import logging
from datetime import datetime
from celery import Celery
from infrastructure.database import database
from infrastructure.repositories.MongoImageRepository import MongoImageRepository
from infrastructure.medical_image_validator import MedicalImageValidator

logger = logging.getLogger(__name__)

# Configuración de Celery
celery_app = Celery('image_service')
celery_app.config_from_object('tasks.celery_config')

@celery_app.task(bind=True)
def validate_medical_image_task(self, image_id: str, file_content: bytes, mime_type: str):
    """Tarea en background para validar si una imagen es una tomografía cerebral"""
    try:
        logger.info(f"Iniciando validación médica para imagen: {image_id}")
        
        # Crear loop de asyncio para ejecutar validación
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Conectar a base de datos
        loop.run_until_complete(database.connect_db())
        repo = MongoImageRepository()
        
        # Actualizar estado a "validating"
        update_data = {
            "processing_status": "validating",
            "metadata.processing_status": "validating",
            "metadata.medical_validation": {
                "status": "processing",
                "descripcion": "Validando si es tomografía cerebral..."
            }
        }
        loop.run_until_complete(repo.update(str(image_id), update_data))
        
        # Ejecutar validación médica con timeout
        try:
            validator = MedicalImageValidator()
            is_valid_ct, validation_info = loop.run_until_complete(
                asyncio.wait_for(
                    validator.validate_brain_ct(file_content, mime_type),
                    timeout=60.0  # Timeout de 60 segundos
                )
            )
            
            # Actualizar resultado de validación
            validation_update = {
                "metadata.medical_validation": {
                    "status": "completed" if is_valid_ct else "failed",
                    "is_valid_ct": is_valid_ct,
                    "descripcion": validation_info.get("descripcion", ""),
                    "completed_at": datetime.utcnow().isoformat()
                }
            }
            loop.run_until_complete(repo.update(str(image_id), validation_update))
            
            if not is_valid_ct:
                logger.warning(f"Validación médica fallida para imagen {image_id}: {validation_info.get('descripcion', '')}")
                # Marcar como fallido - NO continuar con procesamiento
                failed_update = {
                    "processing_status": "failed",
                    "metadata.processing_error": f"La imagen no es una tomografía cerebral válida. {validation_info.get('descripcion', '')}",
                    "metadata.processing_completed": datetime.utcnow().isoformat(),
                    "metadata.processing_status": "failed"
                }
                loop.run_until_complete(repo.update(str(image_id), failed_update))
                return {"status": "failed", "reason": "invalid_medical_image"}
            
            logger.info(f"Validación médica exitosa para imagen: {image_id}")
            
            # Si la validación fue exitosa, iniciar procesamiento de tumor
            analyze_tumor_task.delay(image_id)
            
            return {"status": "success", "next_task": "tumor_analysis"}
            
        except asyncio.TimeoutError:
            logger.error(f"Timeout en validación médica para imagen: {image_id}")
            # Marcar como fallido por timeout - NO continuar con procesamiento
            validation_update = {
                "metadata.medical_validation": {
                    "status": "timeout",
                    "descripcion": "Validación médica tardó demasiado tiempo - no se pudo verificar si es una tomografía cerebral válida",
                    "completed_at": datetime.utcnow().isoformat()
                }
            }
            loop.run_until_complete(repo.update(str(image_id), validation_update))
            
            # Marcar como fallido - NO continuar con procesamiento
            failed_update = {
                "processing_status": "failed",
                "metadata.processing_error": "Validación médica tardó demasiado tiempo. No se pudo verificar si la imagen es una tomografía cerebral válida.",
                "metadata.processing_completed": datetime.utcnow().isoformat(),
                "metadata.processing_status": "failed"
            }
            loop.run_until_complete(repo.update(str(image_id), failed_update))
            return {"status": "failed", "reason": "validation_timeout"}
        
    except Exception as e:
        logger.error(f"Error en validación médica: {str(e)}")
        # Actualizar estado a "failed"
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(database.connect_db())
            repo = MongoImageRepository()
            
            update_data = {
                "processing_status": "failed",
                "metadata.processing_error": f"Error en validación médica: {str(e)}",
                "metadata.processing_completed": datetime.utcnow().isoformat(),
                "metadata.processing_status": "failed",
                "metadata.medical_validation": {
                    "status": "error",
                    "descripcion": f"Error en validación médica: {str(e)}",
                    "completed_at": datetime.utcnow().isoformat()
                }
            }
            loop.run_until_complete(repo.update(str(image_id), update_data))
        except:
            pass
        raise

@celery_app.task(bind=True)
def analyze_tumor_task(self, image_id: str):
    """Tarea en background para analizar tumores en una imagen"""
    try:
        logger.info(f"Iniciando análisis de tumor para imagen: {image_id}")
        
        # Crear loop de asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Conectar a base de datos
        loop.run_until_complete(database.connect_db())
        repo = MongoImageRepository()
        
        # Obtener imagen
        image_entity = loop.run_until_complete(repo.find_by_id(image_id))
        if not image_entity:
            logger.error(f"Imagen no encontrada: {image_id}")
            raise Exception("Imagen no encontrada")
        
        # Actualizar estado a "processing"
        update_data = {
            "processing_status": "processing",
            "metadata.processing_started": datetime.utcnow().isoformat(),
            "metadata.processing_status": "processing"
        }
        loop.run_until_complete(repo.update(str(image_entity.id), update_data))
        
        # Por ahora, marcar como fallido ya que no hay sistema de predicción disponible
        logger.info(f"No hay sistema de predicción disponible para imagen {image_id}")
        raise Exception("Sistema de predicción no disponible")
        
    except Exception as e:
        logger.error(f"Error en análisis de tumor: {str(e)}")
        # Actualizar estado a "failed"
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(database.connect_db())
            repo = MongoImageRepository()
            
            update_data = {
                "processing_status": "failed",
                "metadata.processing_error": str(e),
                "metadata.processing_completed": datetime.utcnow().isoformat(),
                "metadata.processing_status": "failed"
            }
            loop.run_until_complete(repo.update(str(image_entity.id), update_data))
        except:
            pass
        raise
