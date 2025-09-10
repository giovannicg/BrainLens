from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

import logging
from datetime import datetime
from PIL import Image
import io
import numpy as np
from src.predictor import load_models_from_dir, preprocess_image, predict_with_models

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


class PredictionResponse(BaseModel):
    status: str
    prediction: Optional[str] = None
    mean_score: Optional[float] = None
    error: Optional[str] = None
    processing_time: Optional[float] = None

MODELS_PRE_DIR = '/app/modelo_multiclase/pre_clasificacion'
MODELS_POST_DIR = '/app/modelo_multiclase/post_clasificacion'

MODELS_PRE = load_models_from_dir(MODELS_PRE_DIR)
MODELS_POST = load_models_from_dir(MODELS_POST_DIR)

@app.get("/")
async def root():
    return {"message": "BrainLens Local Prediction Service is running."}

@app.get("/models/status")
async def get_models_status():
    """Devuelve el estado de los modelos cargados."""
    return {
        "models": {
            "pre": len(MODELS_PRE),
            "post": len(MODELS_POST)
        }
    }

@app.post("/predict", response_model=PredictionResponse)
async def predict_tumor(image: UploadFile = File(...)):
    """Recibe imagen, realiza predicción con varios modelos y devuelve la media (sí/no)."""
    import time
    start_time = time.time()
    if not MODELS_PRE or not MODELS_POST:
        raise HTTPException(status_code=500, detail="No hay modelos cargados")
    try:
        image_bytes = await image.read()
        logger.info("/predict | filename=%s content_type=%s bytes=%s",
                    getattr(image, "filename", None), getattr(image, "content_type", None), len(image_bytes))
        try:
            pil_img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Imagen inválida: {str(e)}")

        # Predicción con modelos PRE
        scores_pre = predict_with_models(MODELS_PRE, pil_img)
        mean_score = float(np.mean(scores_pre))
        result = "tumor" if mean_score >= 0.5 else "notumor"
        elapsed = time.time() - start_time
        logger.info(f"Predicción: scores={scores_pre} mean={mean_score} resultado={result}")

        # Si no hay tumor, devolver resultado
        if result == "notumor":
            return PredictionResponse(status="success", prediction=result, mean_score=mean_score, processing_time=elapsed)

        # Predicción con modelos POST
        # TODO: definir class_names cuando tengamos los modelos definitivos
        class_names = ['glioma', 'meningioma', 'notumor', 'pituitary']
        predictions_post, scores_post = predict_with_models(MODELS_POST, pil_img, post=True, class_names=class_names)
        if predictions_post:
            from collections import Counter
            most_common_class = Counter(predictions_post).most_common(1)[0][0]
            mean_score = float(np.mean(scores_post))
        else:
            most_common_class = None
            mean_score = None
        logger.info(f"Predicción post: clases={predictions_post} scores={scores_post} clase_final={most_common_class} mean_score={mean_score}")

        return PredictionResponse(status="success", prediction=most_common_class, mean_score=mean_score, processing_time=elapsed)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error en /predict: %s", str(e))
        return PredictionResponse(status="error", error=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
