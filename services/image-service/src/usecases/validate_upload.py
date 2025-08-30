import os
import uuid
import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any
import asyncio

from infrastructure.storage import StorageService
from tasks.validation_tasks import validate_upload_task

logger = logging.getLogger(__name__)

class ValidateUploadUseCase:
    def __init__(self, storage_service: StorageService):
        self.storage_service = storage_service
        logger.info(f"ValidateUploadUseCase inicializado con storage_service: {type(storage_service)}")
        
    async def execute(self, file_content: bytes, original_filename: str, user_id: str, custom_filename: Optional[str] = None) -> str:
        """Fase 1: Subir imagen a staging y lanzar validación en background"""
        try:
            logger.info(f"Iniciando validación de upload para archivo: {original_filename}")
            
            # Validar archivo básico
            if not file_content:
                raise ValueError("El archivo está vacío")
            
            if not self.storage_service.is_valid_image_type(original_filename):
                raise ValueError("Tipo de archivo no válido")
            
            if len(file_content) > self.storage_service.get_max_file_size():
                raise ValueError("El archivo es demasiado grande")
            
            # Generar job_id único
            job_id = str(uuid.uuid4())
            
            # Guardar archivo en staging
            staging_filename = f"staging/{job_id}_{original_filename}"
            staging_path = await self.storage_service.save_to_staging(file_content, staging_filename)
            
            logger.info(f"Archivo guardado en staging: {staging_path}")
            
            # Crear metadata del job
            job_metadata = {
                "job_id": job_id,
                "user_id": user_id,
                "original_filename": original_filename,
                "custom_filename": custom_filename,
                "staging_path": staging_path,
                "file_size": len(file_content),
                "created_at": datetime.utcnow().isoformat(),
                "status": "validating"
            }
            
            # Guardar metadata del job en Redis (simulado con archivo temporal)
            await self._save_job_metadata(job_id, job_metadata)
            
            # Lanzar validación en background
            validate_upload_task.delay(job_id, staging_path, original_filename, user_id, custom_filename)
            
            logger.info(f"Job de validación lanzado: {job_id}")
            
            return job_id
            
        except Exception as e:
            logger.error(f"Error en validate_upload: {str(e)}")
            raise
    
    async def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Obtener estado de un job de validación"""
        try:
            # Obtener metadata del job desde Redis (simulado)
            job_metadata = await self._get_job_metadata(job_id)
            
            if not job_metadata:
                raise ValueError(f"Job no encontrado: {job_id}")
            
            return {
                "status": job_metadata.get("status", "unknown"),
                "message": job_metadata.get("message", ""),
                "image_id": job_metadata.get("image_id"),
                "error": job_metadata.get("error")
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo estado de job {job_id}: {str(e)}")
            raise
    
    async def _save_job_metadata(self, job_id: str, metadata: Dict[str, Any]):
        """Guardar metadata del job (simulado con archivo)"""
        try:
            # En producción, esto sería Redis
            jobs_dir = "/app/storage/jobs"
            os.makedirs(jobs_dir, exist_ok=True)
            
            job_file = os.path.join(jobs_dir, f"{job_id}.json")
            with open(job_file, 'w') as f:
                json.dump(metadata, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error guardando metadata de job: {str(e)}")
            raise
    
    async def _get_job_metadata(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Obtener metadata del job (simulado con archivo)"""
        try:
            # En producción, esto sería Redis
            jobs_dir = "/app/storage/jobs"
            job_file = os.path.join(jobs_dir, f"{job_id}.json")
            
            if not os.path.exists(job_file):
                return None
            
            with open(job_file, 'r') as f:
                return json.load(f)
                
        except Exception as e:
            logger.error(f"Error obteniendo metadata de job: {str(e)}")
            return None
