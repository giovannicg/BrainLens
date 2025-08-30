from pydantic import BaseModel
from typing import Optional

class ValidationJobResponse(BaseModel):
    job_id: str
    status: str
    message: str

class ValidationJobStatusResponse(BaseModel):
    job_id: str
    status: str
    message: str
    image_id: Optional[str] = None
    error: Optional[str] = None
