import logging
logger = logging.getLogger(__name__)
logger.info('[MEDICAL_IMAGE_VALIDATOR] Archivo medical_image_validator.py cargado')
import os
import logging
from typing import Tuple, Dict, Any
from adapters.gateways.vlm_gateway import VisionLanguageGateway

logger = logging.getLogger(__name__)

class MedicalImageValidator:
    logger.info('[MEDICAL_IMAGE_VALIDATOR] Instanciando MedicalImageValidator')
    def __init__(self):
        # Usar system prompt específico para validación
        self.validator_system_prompt = os.getenv(
            "VLM_VALIDATOR_SYSTEM_PROMPT", 
            "Eres un validador médico especializado. Tu única función es responder SÍ o NO a preguntas simples sobre imágenes médicas. Responde siempre de forma clara y directa."
        )
        
        # Crear VLM con system prompt específico para validación
        self.vlm = VisionLanguageGateway()
        # Sobrescribir el system prompt para validación
        self.vlm.system_prompt = self.validator_system_prompt
        
        logger.info(f"MedicalImageValidator inicializado con system prompt: {self.validator_system_prompt[:50]}...")
        
    async def validate_brain_ct(self, image_bytes: bytes, mime_type: str) -> Tuple[bool, Dict[str, Any]]:
        logger.info(f'[MEDICAL_IMAGE_VALIDATOR] validate_brain_ct llamada con mime_type={mime_type}, bytes={len(image_bytes)}')
        """
        Valida si la imagen es una tomografía cerebral (CT) válida.
        
        Returns:
            Tuple[bool, Dict]: (es_valida, informacion_detallada)
        """
        try:
            logger.info("Iniciando validación de imagen médica")
            
            # Prompt simplificado y directo
            validation_prompt = """
            ¿Es esta imagen una tomografía computarizada (CT) del cerebro?
            
            Responde solo: SÍ o NO
            """
            
            # Usar el VLM para analizar la imagen
            response = self.vlm.ask_about_image(
                prompt=validation_prompt,
                image_bytes=image_bytes,
                mime_type=mime_type
            )
            
            logger.info(f"Respuesta del VLM para validación: {response}")
            
            # Analizar respuesta simple
            response_lower = response.lower().strip()
            
            # Buscar respuestas afirmativas
            is_valid = any(keyword in response_lower for keyword in [
                "sí", "si", "yes", "true", "correcto", "correcta", "es una", "tomografía", "ct", "cerebral"
            ])
            
            # Buscar respuestas negativas
            is_invalid = any(keyword in response_lower for keyword in [
                "no", "false", "incorrecto", "incorrecta", "no es", "no es una"
            ])
            
            # Si hay conflicto, ser más estricto
            if is_invalid:
                is_valid = False
            
            validation_result = {
                "es_tomografia_cerebral": is_valid,
                "muestra_estructuras_cerebrales": is_valid,  # Asumir que si es CT cerebral, muestra estructuras
                "calidad_suficiente": is_valid,  # Asumir que si es CT cerebral, tiene calidad suficiente
                "descripcion": f"Respuesta del VLM: {response.strip()}",
                "respuesta_original": response.strip()
            }
            
            logger.info(f"Resultado de validación: {is_valid}")
            logger.info(f"Respuesta original: {response.strip()}")
            
            return is_valid, validation_result
            
        except Exception as e:
            logger.error(f"Error en validación de imagen médica: {str(e)}")
            # En caso de error técnico, marcar para revisión manual
            return False, {
                "es_tomografia_cerebral": False,
                "muestra_estructuras_cerebrales": False,
                "calidad_suficiente": False,
                "descripcion": "Error técnico en validación automática - se requiere revisión manual.",
                "error": str(e),
                "validation_error": True
            }
    
    def _parse_text_response(self, response: str) -> Dict[str, Any]:
        """
        Parsea una respuesta de texto del VLM para extraer información de validación.
        """
        response_lower = response.lower()
        
        # Buscar indicadores en el texto
        is_ct = any(keyword in response_lower for keyword in [
            "tomografía", "tomografia", "ct", "computarizada", "cerebral", "cerebro"
        ])
        
        has_brain_structures = any(keyword in response_lower for keyword in [
            "cerebro", "cerebral", "craneo", "cráneo", "meninges", "ventrículos", "ventriculos"
        ])
        
        good_quality = not any(keyword in response_lower for keyword in [
            "borrosa", "pobre", "mala calidad", "no se ve", "indistinta"
        ])
        
        return {
            "es_tomografia_cerebral": is_ct,
            "muestra_estructuras_cerebrales": has_brain_structures,
            "calidad_suficiente": good_quality,
            "descripcion": response[:200] + "..." if len(response) > 200 else response
        }
