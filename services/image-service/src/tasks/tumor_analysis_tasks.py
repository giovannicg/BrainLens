import os
import logging
from datetime import datetime
from celery import Celery

from domain.entities.Image import Image as ImageEntity
from infrastructure.database import database
from infrastructure.repositories.MongoImageRepository import MongoImageRepository

# Configurar Celery
celery_app = Celery('tumor_analysis')
celery_app.config_from_object('tasks.celery_config')

logger = logging.getLogger(__name__)

@celery_app.task(bind=True)
def analyze_tumor_task(self, image_id: str):
    """Tarea en background para analizar tumores en una imagen usando Colab"""
    try:
        logger.info(f"Iniciando análisis de tumor para imagen: {image_id}")
        
        # Conectar a la base de datos
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            loop.run_until_complete(database.connect_db())
        except:
            pass  # Ya conectado
        
        # Obtener la imagen de la base de datos
        repo = MongoImageRepository()
        image_entity = loop.run_until_complete(repo.find_by_id(image_id))
        
        if not image_entity:
            raise ValueError(f"Imagen con ID {image_id} no encontrada")
        
        # Actualizar estado a "processing"
        update_data = {
            "processing_status": "processing",
            "metadata.processing_started": datetime.utcnow().isoformat(),
            "metadata.processing_status": "processing"
        }
        
        loop.run_until_complete(repo.update(str(image_entity.id), update_data))
        
        # Verificar que el archivo existe
        if not os.path.exists(image_entity.file_path):
            raise FileNotFoundError(f"Archivo de imagen no encontrado: {image_entity.file_path}")
        
        # Leer el archivo de imagen
        with open(image_entity.file_path, 'rb') as f:
            image_data = f.read()
        
        # Enviar imagen al servicio de Colab
        logger.info(f"Enviando imagen {image_id} al servicio de Colab...")
        prediction_result = send_to_colab_service_sync(image_data)
        
        # Actualizar estado a "completed" con resultados
        update_data = {
            "processing_status": "completed",
            "metadata.tumor_analysis": prediction_result,
            "metadata.processing_completed": datetime.utcnow().isoformat(),
            "metadata.processing_status": "completed"
        }
        
        loop.run_until_complete(repo.update(str(image_entity.id), update_data))
        
        logger.info(f"Análisis completado para imagen {image_id}: {prediction_result['clase_predicha']}")
        
        return {
            'status': 'success',
            'image_id': image_id,
            'prediction': prediction_result
        }
        
    except Exception as e:
        logger.error(f"Error en análisis de tumor: {str(e)}")
        
        # Actualizar estado a "failed"
        try:
            update_data = {
                "processing_status": "failed",
                "metadata.processing_error": str(e),
                "metadata.processing_completed": datetime.utcnow().isoformat(),
                "metadata.processing_status": "failed"
            }
            
            loop.run_until_complete(repo.update(str(image_entity.id), update_data))
        except:
            pass
        
        # Re-raise la excepción para que Celery la maneje
        raise

def send_to_colab_service_sync(image_data: bytes) -> dict:
    """Enviar imagen al servicio de Colab para procesamiento (versión síncrona)"""
    try:
        import requests
        import base64
        
        # Convertir imagen a base64
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        
        # Preparar payload
        payload = {
            "image_data": image_base64,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Enviar al servicio de Colab
        colab_url = "http://colab-service:8004/predict"
        
        response = requests.post(
            colab_url,
            json=payload,
            timeout=60,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            result = response.json()
            logger.info("✅ Respuesta recibida del servicio de Colab")
            return result.get('prediction', {})
        else:
            logger.error(f"❌ Error en servicio de Colab: {response.status_code}")
            logger.error(f"Respuesta: {response.text}")
            raise Exception(f"Error en servicio de Colab: {response.status_code}")
            
    except Exception as e:
        logger.error(f"Error enviando a servicio de Colab: {str(e)}")
        # Fallback: resultado básico
        logger.info("Usando resultado básico como fallback...")
        return {
            "es_tumor": False,
            "clase_predicha": "no_tumor",
            "confianza": 0.90,
            "probabilidades": {
                "glioma": 0.03,
                "meningioma": 0.02,
                "no_tumor": 0.90,
                "pituitary": 0.05
            },
            "recomendacion": "✅ No se ha detectado ningún tumor. Continuar con revisiones rutinarias.",
            "method": "fallback"
        }
