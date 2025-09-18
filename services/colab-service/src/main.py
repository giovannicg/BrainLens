from fastapi import FastAPI, HTTPException, UploadFile, File, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import os
import logging
import httpx
import time
import base64
import traceback
import asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuración dinámica de CORS
def get_cors_origins():
    """Configuración dinámica de CORS según el entorno"""
    environment = os.getenv("ENVIRONMENT", "development")
    alb_dns = os.getenv("ALB_DNS_NAME", "")

    if environment == "production" and alb_dns:
        return [f"http://{alb_dns}", f"https://{alb_dns}"]
    else:
        return ["http://localhost:3000", "http://127.0.0.1:3000"]

app = FastAPI(title="BrainLens Colab Proxy Service", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware para headers de caché
@app.middleware("http")
async def add_cache_headers(request: Request, call_next):
    response = await call_next(request)
    
    # Headers de seguridad
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    
    # Configurar caché según el tipo de endpoint
    path = request.url.path
    
    if path in ["/health", "/api/v1/colab/health"]:
        # Health check - sin caché
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    else:
        # APIs de predicción - sin caché (datos dinámicos)
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
    
    return response

@app.get("/health")
async def health():
    return {"status": "ok", "service": "colab"}

# Health endpoint for EKS ingress compatibility
@app.get("/api/v1/colab/health")
async def health_api_v1():
    return {"status": "ok", "service": "colab"}



class PredictionResponse(BaseModel):
    status: str
    prediction: Optional[str] = None
    mean_score: Optional[float] = None
    error: Optional[str] = None
    processing_time: Optional[float] = None


@app.post("/predict", response_model=PredictionResponse)
async def predict_tumor(image: UploadFile = File(...)):
    """Recibe imagen, realiza predicción con varios modelos y devuelve la moda.

    Soporta modelos binarios (sigmoid) y multiclase (softmax). La clase final es la moda
    de las predicciones por modelo. En empate, se elige la clase con mayor media de
    probabilidad entre las empatadas; si persiste empate, la de menor índice.
    """
    start_time = time.time()
    # Siempre usar Colab; si no está configurado, error
    colab_url = os.getenv("COLAB_PREDICT_URL", "").strip()
    if not colab_url:
        raise HTTPException(status_code=500, detail="COLAB_PREDICT_URL no está configurado")
    try:
        image_bytes = await image.read()
        logger.info("/predict (proxy Colab) | filename=%s content_type=%s bytes=%s",
                    getattr(image, "filename", None), getattr(image, "content_type", None), len(image_bytes))
        b64 = base64.b64encode(image_bytes).decode("utf-8")
        headers = {"ngrok-skip-browser-warning": "true", "Content-Type": "application/json"}
        last_err = None
        for attempt in range(1, 3):
            try:
                async with httpx.AsyncClient(timeout=120) as client:
                    resp = await client.post(colab_url, json={"image_data": b64}, headers=headers)
                if resp.status_code >= 400:
                    logger.error("Colab respondió %s: %s", resp.status_code, resp.text[:500])
                    raise HTTPException(status_code=resp.status_code, detail=f"Colab error: {resp.text}")
                break
            except Exception as e:
                last_err = e
                logger.error("Intento %s a Colab falló: %r", attempt, e)
                if attempt < 2:
                    await asyncio.sleep(1.5)
        if last_err and 'resp' not in locals():
            raise last_err
        data = resp.json()
        logger.info("/predict Colab resp: %s", str(data)[:500])
        elapsed = time.time() - start_time
        return PredictionResponse(
            status=str(data.get("status", "success")),
            prediction=data.get("prediction"),
            mean_score=float(data.get("mean_score")) if data.get("mean_score") is not None else None,
            processing_time=float(elapsed),
            error=data.get("error")
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Fallo reenviando a Colab: %r\n%s", e, traceback.format_exc())
        raise HTTPException(status_code=502, detail=f"Error comunicando con Colab: {str(e)}")


@app.post("/predict/raw")
async def predict_tumor_raw(image: UploadFile = File(...)):
    """Proxy a Colab /predict-raw devolviendo detalle de votos y per-model."""
    colab_raw_url = os.getenv("COLAB_PREDICT_RAW_URL", "").strip()
    if not colab_raw_url:
        base = os.getenv("COLAB_PREDICT_URL", "").strip()
        if not base:
            raise HTTPException(status_code=500, detail="COLAB_PREDICT_URL no está configurado")
        if base.endswith("/predict"):
            colab_raw_url = base + "-raw"
        else:
            colab_raw_url = base.rstrip("/") + "/predict-raw"

    try:
        image_bytes = await image.read()
        b64 = base64.b64encode(image_bytes).decode("utf-8")
        headers = {"ngrok-skip-browser-warning": "true", "Content-Type": "application/json"}
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(colab_raw_url, json={"image_data": b64}, headers=headers)
        if resp.status_code >= 400:
            logger.error("Colab (raw) respondió %s: %s", resp.status_code, resp.text[:500])
            raise HTTPException(status_code=resp.status_code, detail=f"Colab error: {resp.text}")
        data = resp.json()
        logger.info("/predict/raw Colab resp: %s", str(data)[:500])
        return data
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Fallo reenviando a Colab (raw): %s", str(e))
        raise HTTPException(status_code=502, detail=f"Error comunicando con Colab (raw): {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
