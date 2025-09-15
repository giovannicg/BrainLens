from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class ImageResponse(BaseModel):
    id: str
    filename: str
    original_filename: str
    file_size: int
    mime_type: str
    width: Optional[int] = None
    height: Optional[int] = None
    user_id: str
    upload_date: datetime
    processing_status: str
    metadata: Optional[Dict[str, Any]] = None

class ImageUploadResponse(BaseModel):
    message: str
    image: Optional[ImageResponse] = None
    processing_status: Optional[str] = Field(None, description="Estado del procesamiento (pending/processing/completed/failed)")
    # Compatibilidad con respuestas previas
    success: Optional[bool] = None
    status: Optional[str] = None
    error_code: Optional[str] = Field(None, description="Código de error específico si fallo")
    error_detail: Optional[str] = Field(None, description="Detalle del error si fallo")

class ImageListResponse(BaseModel):
    images: List[ImageResponse]
    total: int
    skip: int
    limit: int

class ImageDeleteResponse(BaseModel):
    message: str
    deleted: bool

class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None

# DTOs para predicción de tumores
class TumorPredictionResult(BaseModel):
    es_tumor: bool = Field(..., description="Indica si se detectó un tumor")
    clase_predicha: str = Field(..., description="Clase predicha (glioma, meningioma, no_tumor, pituitary)")
    confianza: float = Field(..., description="Confianza de la predicción (0-1)")
    probabilidades: Dict[str, float] = Field(..., description="Probabilidades para cada clase")

class ProcessingStatusResponse(BaseModel):
    image_id: str
    status: str = Field(..., description="Estado del procesamiento")
    message: str = Field(..., description="Mensaje descriptivo")
    prediction: Optional[TumorPredictionResult] = Field(None, description="Resultado de la predicción si está completado")
    processing_started: Optional[datetime] = Field(None, description="Cuándo comenzó el procesamiento")
    processing_completed: Optional[datetime] = Field(None, description="Cuándo se completó el procesamiento")
