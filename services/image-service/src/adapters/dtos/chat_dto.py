from pydantic import BaseModel, Field
from typing import List, Literal, Optional
from datetime import datetime


class ChatMessageDTO(BaseModel):
    id: Optional[str] = Field(default=None)
    image_id: str
    user_id: str
    role: Literal["user", "assistant"]
    content: str
    timestamp: datetime


class ChatHistoryResponse(BaseModel):
    messages: List[ChatMessageDTO]
    total: int


class ChatRequest(BaseModel):
    message: str = Field(..., description="Pregunta del usuario sobre la imagen")


class ChatResponse(BaseModel):
    answer: str
    message: ChatMessageDTO
    history: Optional[List[ChatMessageDTO]] = None


