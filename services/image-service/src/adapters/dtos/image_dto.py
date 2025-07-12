from pydantic import BaseModel
from typing import Optional, List
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
    metadata: dict

class ImageUploadResponse(BaseModel):
    message: str
    image: ImageResponse

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
