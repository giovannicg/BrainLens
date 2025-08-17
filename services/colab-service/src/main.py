from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import os
import asyncio
import logging
from datetime import datetime
import json
import requests
from PIL import Image
import io
import base64

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="BrainLens Colab Service", version="1.0.0")

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ColabConfig(BaseModel):
    notebook_url: str
    google_drive_folder_id: Optional[str] = None
    api_key: Optional[str] = None

class PredictionRequest(BaseModel):
    image_data: str  # Base64 encoded image
    colab_config: ColabConfig

class PredictionResponse(BaseModel):
    status: str
    prediction: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    processing_time: Optional[float] = None

# Configuración global
COLAB_CONFIG = None

@app.get("/health")
async def health_check():
    """Endpoint de salud del servicio"""
    return {
        "status": "healthy",
        "service": "colab-service",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/configure")
async def configure_colab(config: ColabConfig):
    """Configurar el servicio de Colab"""
    global COLAB_CONFIG
    COLAB_CONFIG = config
    logger.info(f"Colab configurado con notebook: {config.notebook_url}")
    return {"status": "configured", "message": "Colab service configured successfully"}

@app.post("/predict", response_model=PredictionResponse)
async def predict_tumor(
    background_tasks: BackgroundTasks,
    image: UploadFile = File(...),
    use_colab: bool = True
):
    """Procesar imagen para detección de tumores usando Colab"""
    
    if not COLAB_CONFIG and use_colab:
        raise HTTPException(status_code=400, detail="Colab no está configurado")
    
    try:
        # Leer la imagen
        image_data = await image.read()
        
        # Verificar que es una imagen válida
        try:
            img = Image.open(io.BytesIO(image_data))
            logger.info(f"Imagen recibida: {img.size} {img.mode}")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Imagen inválida: {str(e)}")
        
        if use_colab:
            try:
                # Procesar con Colab
                result = await process_with_colab(image_data)
            except Exception as e:
                logger.error(f"Error con Colab: {str(e)}")
                raise Exception(f"No se pudo conectar al notebook de Colab: {str(e)}")
        else:
            # Procesar localmente (fallback)
            result = await process_locally(image_data)
        
        return PredictionResponse(
            status="success",
            prediction=result,
            processing_time=result.get("processing_time", 0)
        )
        
    except Exception as e:
        logger.error(f"Error procesando imagen: {str(e)}")
        return PredictionResponse(
            status="error",
            error=str(e)
        )

async def process_with_colab(image_data: bytes) -> Dict[str, Any]:
    """Procesar imagen usando Google Colab"""
    
    start_time = datetime.now()
    
    try:
        # Convertir imagen a base64
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        
        # Preparar datos para enviar a Colab
        payload = {
            "image_data": image_base64,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Enviar a Colab (esto dependerá de cómo configures tu notebook)
        # Opción 1: Usando Google Drive
        if COLAB_CONFIG.google_drive_folder_id:
            result = await send_to_colab_via_drive(image_data, payload)
        else:
            # Opción 2: Usando API directa (si configuras tu notebook para recibir requests)
            result = await send_to_colab_via_api(payload)
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return {
            **result,
            "processing_time": processing_time,
            "method": "colab"
        }
        
    except Exception as e:
        logger.error(f"Error procesando con Colab: {str(e)}")
        raise

async def send_to_colab_via_drive(image_data: bytes, payload: Dict) -> Dict[str, Any]:
    """Enviar imagen a Colab usando Google Drive"""
    
    logger.info("Enviando imagen a Colab via Google Drive...")
    
    try:
        # Aquí implementarías la lógica para subir a Google Drive
        # Por ahora, usamos la API directa como fallback
        logger.warning("Google Drive no configurado, usando API directa...")
        return await send_to_colab_via_api(payload)
        
    except Exception as e:
        logger.error(f"Error enviando a Colab via Drive: {str(e)}")
        raise

async def send_to_colab_via_api(payload: Dict) -> Dict[str, Any]:
    """Enviar imagen a Colab usando API directa"""
    
    logger.info("Enviando imagen a Colab via API...")
    
    try:
        # Usar la URL de ngrok configurada
        if not COLAB_CONFIG.notebook_url:
            raise Exception("URL de Colab no configurada")
        
        # La URL ya debe incluir el protocolo y dominio de ngrok
        colab_url = f"{COLAB_CONFIG.notebook_url}/predict"
        
        logger.info(f"Enviando a: {colab_url}")
        
        # Enviar request al notebook de Colab
        response = await asyncio.get_event_loop().run_in_executor(
            None, 
            lambda: requests.post(
                colab_url,
                json=payload,
                timeout=60,  # Timeout más largo para Colab
                headers={'Content-Type': 'application/json'}
            )
        )
        
        if response.status_code == 200:
            result = response.json()
            logger.info("✅ Respuesta recibida de Colab")
            return result.get('prediction', {})
        else:
            logger.error(f"❌ Error en Colab: {response.status_code}")
            logger.error(f"Respuesta: {response.text}")
            raise Exception(f"Error en Colab: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        logger.error("❌ No se pudo conectar al notebook de Colab")
        logger.error("   Asegúrate de que el notebook esté ejecutándose con el servidor API")
        logger.error("   Y que tengas configurado ngrok o similar para exponer el puerto 8081")
        raise Exception("No se pudo conectar al notebook de Colab")
    except Exception as e:
        logger.error(f"Error enviando a Colab: {str(e)}")
        raise



@app.get("/status")
async def get_status():
    """Obtener estado del servicio"""
    return {
        "status": "running",
        "colab_configured": COLAB_CONFIG is not None,
        "timestamp": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004) 