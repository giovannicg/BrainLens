import os
import base64
import logging
import requests
from typing import Optional
from botocore.config import Config as BotoConfig
import boto3

logger = logging.getLogger(__name__)

class VisionLanguageGateway:
    def __init__(self):
        self.provider = os.getenv("VLM_PROVIDER", "ollama")
        self.model = os.getenv("VLM_MODEL", "llava")  # Solo para Ollama
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.system_prompt = os.getenv("VLM_SYSTEM_PROMPT", "Eres un asistente médico especializado en análisis de imágenes radiológicas.")
        self.force_spanish = os.getenv("VLM_FORCE_SPANISH", "true").lower() == "true"
        self.timeout = int(os.getenv("VLM_TIMEOUT", "60"))  # Timeout en segundos
        # Bedrock
        self.aws_region = os.getenv("AWS_REGION", os.getenv("AWS_DEFAULT_REGION", "us-east-1"))
        self.bedrock_model_id = os.getenv("BEDROCK_MODEL_ID", "amazon.nova-lite-v1:0")
        
        # Log con el modelo correcto según el proveedor
        model_name = self.bedrock_model_id if self.provider == "bedrock" else self.model
        logger.info(f"VLM Gateway inicializado: provider={self.provider}, model={model_name}, timeout={self.timeout}s")
    
    def ask_about_image(self, prompt: str, image_bytes: bytes, mime_type: str) -> str:
        """Hacer una pregunta sobre una imagen usando el VLM configurado"""
        try:
            logger.info(f"Enviando pregunta al VLM: {prompt[:100]}...")
            
            if self.provider == "ollama":
                return self._ask_ollama(prompt, image_bytes, mime_type)
            if self.provider == "bedrock":
                return self._ask_bedrock(prompt, image_bytes, mime_type)
            else:
                raise ValueError(f"Proveedor VLM no soportado: {self.provider}")
                
        except Exception as e:
            logger.error(f"Error en VLM Gateway: {str(e)}")
            raise
    
    def _ask_ollama(self, prompt: str, image_bytes: bytes, mime_type: str) -> str:
        """Hacer pregunta a Ollama"""
        try:
            # Codificar imagen a base64
            image_base64 = base64.b64encode(image_bytes).decode('utf-8')
            logger.info(f"Imagen codificada en base64: {len(image_base64)} caracteres")
            
            # Preparar prompt con instrucciones específicas
            wrapped_prompt = prompt  # Usar el prompt directamente sin wrapper adicional
            
            # Preparar payload para Ollama con formato más simple
            messages = []
            if self.system_prompt:
                messages.append({"role": "system", "content": self.system_prompt})
            
            messages.append({
                "role": "user",
                "content": wrapped_prompt,
                "images": [image_base64]  # Formato más simple para llava
            })
            
            payload = {
                "model": self.model,
                "messages": messages,
                "stream": False
            }
            
            logger.info(f"Enviando request a Ollama: {self.base_url}/api/chat")
            logger.info(f"Modelo: {self.model}")
            logger.info(f"Payload keys: {list(payload.keys())}")
            logger.info(f"Messages count: {len(messages)}")
            logger.info(f"Images count: {len(messages[-1].get('images', []))}")
            
            # Hacer request con timeout configurado
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=self.timeout,  # Usar timeout configurado
                headers={"Content-Type": "application/json"}
            )
            
            logger.info(f"Respuesta recibida de Ollama: status={response.status_code}")
            
            if response.status_code != 200:
                logger.error(f"Error en respuesta de Ollama: {response.status_code} - {response.text}")
                raise Exception(f"Error en respuesta de Ollama: {response.status_code}")
            
            # Parsear respuesta
            response_data = response.json()
            logger.info(f"Respuesta parseada: keys={list(response_data.keys())}")
            
            if "message" in response_data and isinstance(response_data["message"], dict):
                content = response_data["message"].get("content", "").strip()
                logger.info(f"Contenido de respuesta: {content[:200]}...")
                return content
            
            # v0.1.43+ puede devolver una lista de mensajes en stream desactivado
            if "messages" in response_data and isinstance(response_data["messages"], list) and response_data["messages"]:
                content = response_data["messages"][-1].get("content", "").strip()
                logger.info(f"Contenido de respuesta (messages): {content[:200]}...")
                return content.strip()
            
            logger.warning("No se encontró respuesta válida en la respuesta de Ollama")
            return ""
            
        except requests.exceptions.Timeout:
            logger.error(f"Timeout en request a Ollama después de {self.timeout} segundos")
            raise Exception(f"Timeout en VLM después de {self.timeout} segundos")
        except requests.exceptions.RequestException as e:
            logger.error(f"Error de red en request a Ollama: {str(e)}")
            raise Exception(f"Error de red en VLM: {str(e)}")
        except Exception as e:
            logger.error(f"Error inesperado en Ollama: {str(e)}")
            raise

    def _ask_bedrock(self, prompt: str, image_bytes: bytes, mime_type: str) -> str:
        """Hacer pregunta a AWS Bedrock (Nova vision)."""
        try:
            logger.info(f"Enviando request a Bedrock model={self.bedrock_model_id} region={self.aws_region}")
            # Bedrock converse API
            client = boto3.client(
                "bedrock-runtime",
                region_name=self.aws_region,
                config=BotoConfig(read_timeout=self.timeout, retries={"max_attempts": 2})
            )

            # Construir contenido: Bedrock Nova solo permite roles 'user' o 'assistant'
            # Inyectamos el system prompt como prefijo del mensaje de usuario
            combined_text = f"{self.system_prompt}\n\n{prompt}" if self.system_prompt else prompt
            user_parts = [{"text": combined_text}]

            # Imagen como bytes (Nova acepta bytes con formato)
            img_format = "png" if "/png" in mime_type or mime_type.endswith("png") else "jpeg"
            image_part = {
                "image": {
                    "format": img_format,
                    "source": {"bytes": image_bytes}
                }
            }
            user_parts.append(image_part)

            messages = [{"role": "user", "content": user_parts}]

            resp = client.converse(
                modelId=self.bedrock_model_id,
                messages=messages,
                inferenceConfig={
                    "maxTokens": 256,
                    "temperature": 0.2,
                },
            )

            # Parsear salida
            output = resp.get("output", {})
            message = output.get("message", {})
            content = message.get("content", [])
            for part in content:
                if "text" in part:
                    return part["text"].strip()
            # Fallback en caso de diferentes formatos
            text = output.get("text") or ""
            return (text or "").strip()

        except Exception as e:
            logger.error(f"Error en Bedrock VLM: {e}")
            raise Exception(f"Error en Bedrock VLM: {str(e)}")


