from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator, model_validator
from bson import ObjectId


from pydantic_core import core_schema
from pydantic import GetCoreSchemaHandler

class AnnotationPoint(BaseModel):
    x: float
    y: float

class AnnotationShape(BaseModel):
    type: str  # "rectangle", "circle", "polygon", "point"
    points: List[AnnotationPoint]
    properties: Dict[str, Any] = Field(default_factory=dict)

class Annotation(BaseModel):
    """Modelo de dominio para una anotación médica."""
    id: Optional[str] = Field(default=None, alias="_id")
    image_id: str
    user_id: str
    title: str
    description: str
    category: str  # "tumor", "vessel", "tissue", "lesion", etc.
    confidence: float = Field(ge=0.0, le=1.0, default=1.0)
    status: str = "pending"  # pending, approved, rejected, completed
    shapes: List[AnnotationShape] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    review_notes: Optional[str] = None
    
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str},
        "json_schema_extra": {
            "example": {
                "image_id": "image123",
                "user_id": "user456",
                "title": "Tumor Detection",
                "description": "Anomalía detectada en lóbulo frontal derecho",
                "category": "tumor",
                "confidence": 0.95,
                "status": "pending",
                "shapes": [
                    {
                        "type": "rectangle",
                        "points": [
                            {"x": 100, "y": 100},
                            {"x": 200, "y": 200}
                        ],
                        "properties": {
                            "color": "#FF0000",
                            "thickness": 2
                        }
                    }
                ],
                "metadata": {
                    "ai_generated": True,
                    "model_version": "v1.0"
                }
            }
        }
    }
