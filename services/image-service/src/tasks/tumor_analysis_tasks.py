import os
import io
import numpy as np
import tensorflow as tf
from PIL import Image
from typing import Dict, Any, Optional
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

class TumorAnalysisProcessor:
    def __init__(self):
        self.model = None
        self.img_size = 300  # Tamaño requerido por EfficientNetB3
        self.classes = ['glioma', 'meningioma', 'no_tumor', 'pituitary']
        
    def _load_model(self):
        """Carga el modelo entrenado"""
        try:
            model_path = os.getenv("MODEL_PATH", "modelo_multiclase.h5")
            if not os.path.exists(model_path):
                raise FileNotFoundError(f"Modelo no encontrado en: {model_path}")
            
            # Intentar cargar el modelo con compile=False para evitar problemas de compatibilidad
            try:
                self.model = tf.keras.models.load_model(model_path, compile=False)
                logger.info(f"Modelo cargado exitosamente desde: {model_path} con compile=False")
            except Exception as e1:
                logger.warning(f"Error cargando con compile=False: {str(e1)}")
                # Si falla, intentar cargar normalmente
                self.model = tf.keras.models.load_model(model_path)
                logger.info(f"Modelo cargado exitosamente desde: {model_path}")
            
            # Recompilar el modelo si es necesario
            if not hasattr(self.model, 'optimizer') or self.model.optimizer is None:
                self.model.compile(
                    optimizer='adam',
                    loss='categorical_crossentropy',
                    metrics=['accuracy']
                )
                logger.info("Modelo recompilado")
            
            return True
        except Exception as e:
            logger.error(f"Error cargando el modelo: {str(e)}")
            raise
    
    def _preprocess_image(self, image_data: bytes) -> np.ndarray:
        """Preprocesa la imagen para el modelo"""
        try:
            # Cargar imagen desde bytes
            image = Image.open(io.BytesIO(image_data))
            
            # Convertir a RGB si es necesario
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Redimensionar
            image = image.resize((self.img_size, self.img_size))
            
            # Convertir a array y normalizar
            img_array = np.array(image)
            img_array = img_array / 255.0
            
            # Añadir dimensión de batch
            img_array = np.expand_dims(img_array, axis=0)
            
            return img_array
            
        except Exception as e:
            logger.error(f"Error preprocesando imagen: {str(e)}")
            raise
    
    def _make_prediction(self, img_array: np.ndarray) -> Dict[str, Any]:
        """Realiza la predicción con el modelo"""
        try:
            if self.model is None:
                self._load_model()
            
            # Hacer predicción
            predictions = self.model.predict(img_array, verbose=0)
            clase_predicha_idx = np.argmax(predictions[0])
            confianza = float(predictions[0][clase_predicha_idx])
            
            # Determinar si es tumor
            es_tumor = clase_predicha_idx != 2  # índice 2 corresponde a 'no_tumor'
            
            # Crear diccionario de probabilidades
            probabilidades = {
                clase: float(prob) 
                for clase, prob in zip(self.classes, predictions[0])
            }
            
            # Generar recomendación
            if es_tumor:
                recomendacion = "⚠️ Se ha detectado un tumor cerebral. Se recomienda consultar con un médico especialista inmediatamente."
            else:
                recomendacion = "✅ No se ha detectado ningún tumor. Continuar con revisiones rutinarias."
            
            return {
                'es_tumor': es_tumor,
                'clase_predicha': self.classes[clase_predicha_idx],
                'confianza': confianza,
                'probabilidades': probabilidades,
                'recomendacion': recomendacion
            }
            
        except Exception as e:
            logger.error(f"Error en predicción: {str(e)}")
            raise

@celery_app.task(bind=True)
def analyze_tumor_task(self, image_id: str):
    """Tarea en background para analizar tumores en una imagen"""
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
        
        # Procesar imagen
        processor = TumorAnalysisProcessor()
        img_array = processor._preprocess_image(image_data)
        prediction_result = processor._make_prediction(img_array)
        
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
