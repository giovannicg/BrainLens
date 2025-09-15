from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class AnnotationPointResponse(BaseModel):
    x: float
    y: float

class AnnotationShapeResponse(BaseModel):
    type: str
    points: List[AnnotationPointResponse]
    properties: Dict[str, Any]

class AnnotationResponse(BaseModel):
    id: str
    image_id: str
    user_id: str
    title: str
    description: str
    category: str
    confidence: float
    status: str
    shapes: List[AnnotationShapeResponse]
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    review_notes: Optional[str] = None

class CreateAnnotationRequest(BaseModel):
    image_id: str
    user_id: str
    title: str
    description: str
    category: str
    confidence: float = 1.0
    status: str = "pending"
    shapes: List[AnnotationShapeResponse] = []
    metadata: Dict[str, Any] = {}

class UpdateAnnotationRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    confidence: Optional[float] = None
    shapes: Optional[List[AnnotationShapeResponse]] = None
    status: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class ReviewAnnotationRequest(BaseModel):
    status: str  # "approved", "rejected"
    review_notes: Optional[str] = None

class AnnotationListResponse(BaseModel):
    annotations: List[AnnotationResponse]
    total: int
    skip: int
    limit: int

class AnnotationCreateResponse(BaseModel):
    message: str
    annotation: AnnotationResponse

class AnnotationUpdateResponse(BaseModel):
    message: str
    annotation: AnnotationResponse

class AnnotationDeleteResponse(BaseModel):
    message: str
    deleted: bool

class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
