import os
import io
import numpy as np
import tensorflow as tf
from PIL import Image
from typing import Dict, Any, Optional
import logging

from domain.entities.Image import Image as ImageEntity
from domain.repositories.ImageRepository import ImageRepository

logger = logging.getLogger(__name__)

class AnalyzeTumorUseCase:
    def __init__(self, image_repository: ImageRepository):
        self.image_repository = image_repository
        self.model = None
        self.img_size = 300  # Tamaño requerido por EfficientNetB3
        self.classes = ['glioma', 'meningioma', 'no_tumor', 'pituitary']
        self.expected_channels = None
        
    def _load_model(self):
        """Carga el modelo entrenado"""
        try:
            model_path = os.getenv("MODEL_PATH", "modelo_multiclase.h5")
            if not os.path.exists(model_path):
                raise FileNotFoundError(f"Modelo no encontrado en: {model_path}")
            
            self.model = tf.keras.models.load_model(model_path)
            # Detect expected input channels from the model's input shape
            try:
                if hasattr(self.model, 'input_shape') and self.model.input_shape is not None:
                    # Expecting shape like (None, H, W, C)
                    self.expected_channels = int(self.model.input_shape[-1]) if len(self.model.input_shape) >= 4 else 3
                else:
                    self.expected_channels = 3
            except Exception:
                self.expected_channels = 3
            logger.info(f"Modelo cargado: input_shape={self.model.input_shape}, expected_channels={self.expected_channels}")
            logger.info(f"Modelo cargado exitosamente desde: {model_path}")
            return True
        except Exception as e:
            logger.error(f"Error cargando el modelo: {str(e)}")
            raise
    
    def _preprocess_image(self, image_data: bytes) -> np.ndarray:
        """Preprocesa la imagen para el modelo"""
        try:
            # Ensure we know how many channels the model expects
            if self.expected_channels is None:
                self._load_model()

            # Cargar imagen desde bytes
            image = Image.open(io.BytesIO(image_data))

            # Convert according to expected channels (1=grayscale, 3=RGB)
            if self.expected_channels == 1:
                # Convert any input (RGB/RGBA/L/LA) to single-channel L
                image = image.convert('L')
            else:
                # Convert any input (L/LA/RGBA/RGB) to 3-channel RGB
                image = image.convert('RGB')

            # Redimensionar
            image = image.resize((self.img_size, self.img_size), resample=Image.BILINEAR)

            # Convert to numpy and ensure shape (H, W, C)
            img_array = np.array(image)
            if img_array.ndim == 2:
                # Expand grayscale to (H, W, 1) or (H, W, 3)
                if self.expected_channels == 1:
                    img_array = np.expand_dims(img_array, axis=-1)
                else:
                    img_array = np.stack([img_array, img_array, img_array], axis=-1)
            elif img_array.ndim == 3 and img_array.shape[-1] == 4:
                # Drop alpha if present
                img_array = img_array[..., :3]

            # If shapes still mismatch, fix by repeating/averaging channels
            if self.expected_channels == 1 and img_array.shape[-1] == 3:
                # Luminosity method to grayscale
                r, g, b = img_array[..., 0], img_array[..., 1], img_array[..., 2]
                gray = 0.299 * r + 0.587 * g + 0.114 * b
                img_array = np.expand_dims(gray, axis=-1)
            elif self.expected_channels == 3 and img_array.shape[-1] == 1:
                img_array = np.repeat(img_array, 3, axis=-1)

            # Convert dtype and normalize
            img_array = img_array.astype('float32') / 255.0

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
    
    async def execute(self, image_id: str) -> Dict[str, Any]:
        """Ejecuta el análisis de tumor para una imagen específica"""
        try:
            logger.info(f"Iniciando análisis de tumor para imagen: {image_id}")

            # Ensure model is loaded before preprocessing (needed for expected_channels)
            if self.model is None:
                self._load_model()
            
            # Obtener la imagen de la base de datos
            image_entity = await self.image_repository.get_by_id(image_id)
            if not image_entity:
                raise ValueError(f"Imagen con ID {image_id} no encontrada")
            
            # Verificar que el archivo existe
            if not os.path.exists(image_entity.file_path):
                raise FileNotFoundError(f"Archivo de imagen no encontrado: {image_entity.file_path}")
            
            # Leer el archivo de imagen
            with open(image_entity.file_path, 'rb') as f:
                image_data = f.read()
            
            # Preprocesar imagen
            img_array = self._preprocess_image(image_data)
            
            # Hacer predicción
            prediction_result = self._make_prediction(img_array)
            
            # Actualizar estado de procesamiento en la base de datos
            image_entity.processing_status = "analyzed"
            if not image_entity.metadata:
                image_entity.metadata = {}
            image_entity.metadata['tumor_analysis'] = prediction_result
            image_entity.metadata['analysis_timestamp'] = str(np.datetime64('now'))
            
            await self.image_repository.update(image_entity)
            
            logger.info(f"Análisis completado para imagen {image_id}: {prediction_result['clase_predicha']}")
            
            return {
                'image': image_entity,
                'prediction': prediction_result
            }
            
        except Exception as e:
            logger.error(f"Error en análisis de tumor: {str(e)}")
            raise
