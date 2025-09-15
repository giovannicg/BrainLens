from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import os
import logging
from datetime import datetime
from PIL import Image
import io
import numpy as np
import tensorflow as tf

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="BrainLens Local Prediction Service", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    return {"status": "ok", "service": "colab"}



class PredictionResponse(BaseModel):
    status: str
    prediction: Optional[str] = None
    mean_score: Optional[float] = None
    error: Optional[str] = None
    processing_time: Optional[float] = None

MODELS_DIR = '/app/modelo_multiclase'
MODEL_PATHS = [
    os.path.join(MODELS_DIR, fname)
    for fname in os.listdir(MODELS_DIR)
    if fname.endswith('.keras')
]
MODELS = []
for path in MODEL_PATHS:
    try:
        model = tf.keras.models.load_model(path)
        # Solo usar modelos con input_shape[-1] == 3 (RGB)
        input_shape = model.input_shape
        if len(input_shape) == 4 and input_shape[-1] == 3:
            MODELS.append(model)
            logging.info(f"Modelo cargado: {path}")
        else:
            logging.warning(f"Modelo ignorado por input_shape incompatible: {path} (input_shape={input_shape})")
    except Exception as e:
        logging.error(f"Error cargando modelo {path}: {e}")


@app.post("/predict", response_model=PredictionResponse)
async def predict_tumor(image: UploadFile = File(...)):
    """Recibe imagen, realiza predicción con varios modelos y devuelve la media (sí/no)."""
    import time
    start_time = time.time()
    if not MODELS:
        raise HTTPException(status_code=500, detail="No hay modelos cargados")
    try:
        image_bytes = await image.read()
        logger.info("/predict | filename=%s content_type=%s bytes=%s",
                    getattr(image, "filename", None), getattr(image, "content_type", None), len(image_bytes))
        try:
            pil_img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Imagen inválida: {str(e)}")


        # Realizar predicción con cada modelo, adaptando el formato de entrada
        scores: List[float] = []
        for model in MODELS:
            input_shape = model.input_shape
            # input_shape: (None, alto, ancho, canales)
            if len(input_shape) == 4:
                _, h, w, c = input_shape
            else:
                h, w, c = 224, 224, 3

            img_model = pil_img.resize((w, h))
            if c == 1:
                img_model = img_model.convert("L")
            else:
                img_model = img_model.convert("RGB")
            arr_model = np.array(img_model) / 255.0
            if c == 1 and arr_model.ndim == 2:
                arr_model = np.expand_dims(arr_model, axis=-1)
            arr_model = np.expand_dims(arr_model, axis=0)

            try:
                pred = model.predict(arr_model)
                score = float(pred.flatten()[0])
                scores.append(score)
            except Exception as e:
                logger.error(f"Error en predicción con modelo {model.name}: {e}")


        mean_score = float(np.mean(scores))
        result = "sí" if mean_score >= 0.5 else "no"
        elapsed = time.time() - start_time
        logger.info(f"Predicción: scores={scores} mean={mean_score} resultado={result}")
        return PredictionResponse(status="success", prediction=result, mean_score=mean_score, processing_time=elapsed)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error en /predict: %s", str(e))
        return PredictionResponse(status="error", error=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
