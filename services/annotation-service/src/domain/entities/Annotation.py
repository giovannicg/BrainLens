from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from bson import ObjectId

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")

class AnnotationPoint(BaseModel):
    x: float
    y: float

class AnnotationShape(BaseModel):
    type: str  # "rectangle", "circle", "polygon", "point"
    points: List[AnnotationPoint]
    properties: Dict[str, Any] = Field(default_factory=dict)

class Annotation(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
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
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        schema_extra = {
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
