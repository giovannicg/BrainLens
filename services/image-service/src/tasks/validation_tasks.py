import logging
logger = logging.getLogger(__name__)
logger.info('[VALIDATION_TASK] Archivo validation_tasks.py cargado')
import os
import json
import asyncio
import logging
from datetime import datetime
from celery import Celery
from infrastructure.database import database
from infrastructure.repositories.MongoImageRepository import MongoImageRepository
from infrastructure.medical_image_validator import MedicalImageValidator
from domain.entities.Image import Image as ImageEntity

logger = logging.getLogger(__name__)

# Configuración de Celery
celery_app = Celery('validation_service')
celery_app.config_from_object('tasks.celery_config')

async def _update_job_status(job_id: str, status: str, message: str, image_id: str = None):
    """Actualizar estado del job"""
    try:
        jobs_dir = "/app/storage/jobs"
        job_file = os.path.join(jobs_dir, f"{job_id}.json")
        
        if os.path.exists(job_file):
            with open(job_file, 'r') as f:
                metadata = json.load(f)
            
            metadata["status"] = status
            metadata["message"] = message
            metadata["completed_at"] = datetime.utcnow().isoformat()
            if image_id:
                metadata["image_id"] = image_id
            
            with open(job_file, 'w') as f:
                json.dump(metadata, f, indent=2)
                
    except Exception as e:
        logger.error(f"Error actualizando estado de job: {str(e)}")

async def _move_to_permanent_storage(file_content: bytes, original_filename: str, user_id: str):
    """Mover archivo de staging a almacenamiento definitivo"""
    # Simular movimiento a almacenamiento definitivo
    # En producción, esto movería el archivo de staging/ a permanent/
    from infrastructure.storage import StorageService
    storage_service = StorageService()
    return await storage_service.save_image(file_content, original_filename, user_id)

@celery_app.task(bind=True)
def validate_upload_task(self, job_id: str, staging_path: str, original_filename: str, user_id: str, custom_filename: str = None):
    """Tarea en background para validar upload y mover a almacenamiento definitivo"""
    try:
        logger.info(f"Iniciando validación de upload para job: {job_id}")
        
        # Crear loop de asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Conectar a base de datos
        loop.run_until_complete(database.connect_db())
        repo = MongoImageRepository()
        
        # Actualizar estado del job
        loop.run_until_complete(_update_job_status(job_id, "validating", "Validación médica en progreso..."))
        
        # Leer archivo desde staging
        with open(staging_path, 'rb') as f:
            file_content = f.read()
        
        # Determinar MIME type
        import mimetypes
        mime_type, _ = mimetypes.guess_type(original_filename)
        if not mime_type:
            mime_type = "application/octet-stream"
        
        # Ejecutar validación médica
        try:
            validator = MedicalImageValidator()
            is_valid_ct, validation_info = loop.run_until_complete(
                asyncio.wait_for(
                    validator.validate_brain_ct(file_content, mime_type),
                    timeout=120.0  # Timeout de 120 segundos
                )
            )
            
            if not is_valid_ct:
                logger.warning(f"Validación médica fallida para job {job_id}: {validation_info.get('descripcion', '')}")
                loop.run_until_complete(_update_job_status(
                    job_id, 
                    "failed", 
                    f"La imagen no es una tomografía cerebral válida. {validation_info.get('descripcion', '')}"
                ))
                # Limpiar archivo de staging
                os.remove(staging_path)
                return {"status": "failed", "reason": "invalid_medical_image"}
            
            logger.info(f"Validación médica exitosa para job: {job_id}")
            
            # Si es válida, mover a almacenamiento definitivo y crear imagen
            final_filename, file_info = loop.run_until_complete(
                _move_to_permanent_storage(file_content, original_filename, user_id)
            )
            
            # Crear entidad de imagen
            image = ImageEntity(
                filename=final_filename,
                original_filename=custom_filename if custom_filename else original_filename,
                file_path=file_info["file_path"],
                file_size=file_info["file_size"],
                mime_type=file_info["mime_type"],
                width=file_info["width"],
                height=file_info["height"],
                user_id=user_id,
                upload_date=datetime.utcnow(),
                processing_status="completed",
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
            
            # Guardar en base de datos
            saved_image = loop.run_until_complete(repo.save(image))

            # Lanzar tarea de análisis de tumor en background
            try:
                from tasks.tumor_analysis_tasks import analyze_tumor_task
                logger.info(f"Lanzando tarea de análisis de tumor para imagen ID: {saved_image.id} en la cola 'tumor_analysis'")
                analyze_tumor_task.apply_async(args=[str(saved_image.id)], queue='tumor_analysis')
                logger.info(f"Tarea de análisis de tumor lanzada correctamente para imagen ID: {saved_image.id}")
            except Exception as e:
                logger.error(f"No se pudo lanzar la tarea de análisis de tumor: {str(e)}")

            # Limpiar archivo de staging
            os.remove(staging_path)

            # Actualizar job como completado
            loop.run_until_complete(_update_job_status(
                job_id,
                "completed",
                "Validación exitosa. Imagen guardada correctamente.",
                str(saved_image.id)
            ))

            logger.info(f"Job {job_id} completado exitosamente. Imagen ID: {saved_image.id}")
            return {"status": "success", "image_id": str(saved_image.id)}
            
        except asyncio.TimeoutError:
            logger.error(f"Timeout en validación médica para job: {job_id}")
            loop.run_until_complete(_update_job_status(
                job_id, 
                "failed", 
                "Validación médica tardó demasiado tiempo. No se pudo verificar si la imagen es una tomografía cerebral válida."
            ))
            # Limpiar archivo de staging
            os.remove(staging_path)
            return {"status": "failed", "reason": "validation_timeout"}
        
    except Exception as e:
        logger.error(f"Error en validación de upload para job {job_id}: {str(e)}")
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(_update_job_status(job_id, "failed", f"Error en validación: {str(e)}"))
            # Limpiar archivo de staging si existe
            if os.path.exists(staging_path):
                os.remove(staging_path)
        except:
            pass
        raise
