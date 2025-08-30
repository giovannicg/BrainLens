from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import os
import logging
from datetime import datetime
from PIL import Image
import io
import base64
import asyncio
import requests

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="BrainLens Colab Proxy Service", version="1.0.0")

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


class PredictionResponse(BaseModel):
    status: str
    prediction: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    processing_time: Optional[float] = None


# Configuración global (solo Colab)
COLAB_CONFIG: Optional[ColabConfig] = None
env_colab_url = os.getenv("COLAB_NOTEBOOK_URL")
if env_colab_url:
    COLAB_CONFIG = ColabConfig(notebook_url=env_colab_url)


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "colab-service",
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/status")
async def get_status():
    return {
        "status": "running",
        "colab_configured": bool(COLAB_CONFIG and COLAB_CONFIG.notebook_url),
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.post("/configure")
def configure_colab(config: ColabConfig):
    """Configurar o actualizar la URL del notebook de Colab"""
    global COLAB_CONFIG
    COLAB_CONFIG = config
    logger.info("Colab configurado con URL: %s", config.notebook_url)
    return {"status": "configured"}


@app.post("/predict", response_model=PredictionResponse)
async def predict_tumor(image: UploadFile = File(...)):
    """Proxy: recibe imagen (multipart 'image'), la envía a Colab y devuelve su respuesta."""
    if not (COLAB_CONFIG and COLAB_CONFIG.notebook_url):
        raise HTTPException(status_code=400, detail="Colab no está configurado")

    try:
        # Leer bytes
        image_bytes = await image.read()
        logger.info("/predict | filename=%s content_type=%s bytes=%s",
                    getattr(image, "filename", None), getattr(image, "content_type", None), len(image_bytes))

        # Validar que es imagen (sanity check)
        try:
            test_img = Image.open(io.BytesIO(image_bytes))
            logger.info("Imagen válida: size=%sx%s mode=%s", *test_img.size, test_img.mode)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Imagen inválida: {str(e)}")

        # Preparar payload base64 para Colab
        image_base64 = base64.b64encode(image_bytes).decode("utf-8")
        payload = {"image_data": image_base64}

        # Enviar a Colab
        url = f"{COLAB_CONFIG.notebook_url.rstrip('/')}/predict"
        logger.info("POST Colab %s | payload_len=%s", url, len(image_base64))

        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: requests.post(url, json=payload, timeout=60, headers={"Content-Type": "application/json"}),
        )

        if response.status_code != 200:
            logger.error("Colab status=%s body=%s", response.status_code, response.text)
            raise HTTPException(status_code=502, detail=f"Error en Colab: {response.status_code}")

        data = response.json()
        logger.info("Respuesta Colab OK")
        return PredictionResponse(status="success", prediction=data.get("prediction", {}))

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error en /predict: %s", str(e))
        return PredictionResponse(status="error", error=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
