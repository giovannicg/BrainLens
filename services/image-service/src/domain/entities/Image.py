from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from bson import ObjectId

class Image(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
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
        "json_encoders": {ObjectId: str}
    }
