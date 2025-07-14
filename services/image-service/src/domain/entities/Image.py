from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator
from bson import ObjectId

class PyObjectId(ObjectId):
    @classmethod
    @field_validator('value')
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema):
        field_schema.update(type="string")

class Image(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    filename: str
    original_filename: str
    file_path: str
    file_size: int
    mime_type: str
    width: Optional[int] = None
    height: Optional[int] = None
    user_id: str
    upload_date: datetime = Field(default_factory=datetime.utcnow)
    processing_status: str = "pending"  # pending, processing, completed, failed
    metadata: dict = Field(default_factory=dict)

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str},
        "json_schema_extra": {
            "example": {
                "filename": "brain_scan_001.jpg",
                "original_filename": "patient_scan.jpg",
                "file_path": "/storage/images/brain_scan_001.jpg",
                "file_size": 2048576,
                "mime_type": "image/jpeg",
                "width": 512,
                "height": 512,
                "user_id": "user123",
                "processing_status": "completed",
                "metadata": {
                    "patient_id": "P001",
                    "scan_type": "MRI",
                    "body_part": "brain"
                }
            }
        }
    }
