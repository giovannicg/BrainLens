# Refactorizado para usar Kafka
import os
import json
import asyncio
import logging
from datetime import datetime
import requests
from infrastructure.database import database
from infrastructure.repositories.MongoImageRepository import MongoImageRepository
from infrastructure.medical_image_validator import MedicalImageValidator
from domain.entities.Image import Image as ImageEntity
from .kafka_producer import ImageKafkaProducer

logger = logging.getLogger(__name__)
producer = ImageKafkaProducer()

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

def send_validate_upload_task(job_id: str, staging_path: str, original_filename: str, user_id: str, custom_filename: str = None):
    """Envia tarea de validación/upload a Kafka"""
    logger.info(f"Enviando tarea a Kafka: job_id={job_id}, staging_path={staging_path}, original_filename={original_filename}, user_id={user_id}, custom_filename={custom_filename}")
    try:
        producer.send('validate_upload', {
            'job_id': job_id,
            'staging_path': staging_path,
            'original_filename': original_filename,
            'user_id': user_id,
            'custom_filename': custom_filename
        })
        logger.info(f"Tarea enviada a Kafka correctamente para job_id={job_id}")
    except Exception as e:
        logger.error(f"Error enviando tarea a Kafka para job_id={job_id}: {str(e)}")

def validate_upload_task(job_id: str, staging_path: str, original_filename: str, user_id: str, custom_filename: str = None):
    """Procesa la tarea de validación/upload recibida desde Kafka"""
    # Validación de parámetros
    if not all([job_id, staging_path, original_filename, user_id]):
        logger.error(f"Parámetros faltantes en tarea de validación/upload: job_id={job_id}, staging_path={staging_path}, original_filename={original_filename}, user_id={user_id}")
        return {"status": "failed", "reason": "missing_parameters"}

    logger.info(f"Iniciando validación de upload para job: {job_id}")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(database.connect_db())
        repo = MongoImageRepository()
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
                processing_status="processing",
                metadata={
                    "processing_started": datetime.utcnow().isoformat(),
                    "processing_status": "processing",
                    "medical_validation": {
                        "status": "completed",
                        "is_valid_ct": True,
                        "descripcion": validation_info.get("descripcion", "Validación médica exitosa"),
                        "completed_at": datetime.utcnow().isoformat()
                    },
                    **file_info["metadata"]
                }
            )
            
            # Guardar en base de datos
            saved_image = loop.run_until_complete(repo.save(image))
            
            # Llamada a colab-service para predicción de tumores con reintentos
            colab_url = os.getenv("COLAB_SERVICE_URL", "http://colab-service:8004")
            predict_endpoint = f"{colab_url}/predict"
            pred_success = False
            pred_error = None
            
            for attempt in range(3):
                try:
                    with open(file_info["file_path"], "rb") as f:
                        file_bytes = f.read()
                    files = {"image": (original_filename, file_bytes, file_info["mime_type"])}
                    resp = requests.post(predict_endpoint, files=files, timeout=120)
                    resp.raise_for_status()
                    pdata = resp.json()
                    
                    status = pdata.get("status", "error")
                    mean_score = pdata.get("mean_score")
                    binary_pred = pdata.get("prediction")
                    
                    es_tumor = True if binary_pred == "sí" else False
                    confianza = float(mean_score) if mean_score is not None else 0.0
                    probabilidades = {"tumor": confianza, "no_tumor": float(1.0 - confianza)}
                    clase_predicha = "glioma" if es_tumor else "no_tumor"
                    recomendacion = (
                        "Derivar a especialista y realizar evaluación adicional" if es_tumor 
                        else "Continuar control rutinario"
                    )
                    
                    # Actualizar imagen con resultados de predicción
                    loop.run_until_complete(repo.update(str(saved_image.id), {
                        "processing_status": "completed" if status == "success" else "failed",
                        "metadata.processing_status": "completed" if status == "success" else "failed",
                        "metadata.processing_completed": datetime.utcnow().isoformat(),
                        "metadata.tumor_analysis": {
                            "es_tumor": es_tumor,
                            "clase_predicha": clase_predicha,
                            "confianza": confianza,
                            "probabilidades": probabilidades,
                            "recomendacion": recomendacion,
                        },
                        "metadata.colab_prediction": pdata,
                    }))
                    pred_success = True
                    break
                    
                except Exception as pred_err:
                    pred_error = pred_err
                    logger.error(f"Error llamando colab-service (intento {attempt+1}/3): {pred_err}")
            
            if not pred_success:
                # Si falla la predicción, marcar como fallida pero mantener la imagen
                loop.run_until_complete(repo.update(str(saved_image.id), {
                    "processing_status": "failed",
                    "metadata.processing_status": "failed",
                    "metadata.processing_completed": datetime.utcnow().isoformat(),
                    "metadata.processing_error": f"Error en predicción: {pred_error}",
                }))
            
            # Limpiar archivo de staging
            try:
                os.remove(staging_path)
            except Exception as rm_err:
                logger.error(f"Error eliminando archivo de staging: {rm_err}")
            
            # Actualizar job como completado
            loop.run_until_complete(_update_job_status(
                job_id, 
                "completed", 
                "Validación y predicción completadas." if pred_success else "Validación completada, predicción falló.", 
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
