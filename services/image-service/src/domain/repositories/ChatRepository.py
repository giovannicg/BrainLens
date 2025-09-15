from abc import ABC, abstractmethod
from typing import List
from ..entities.ChatMessage import ChatMessage


class ChatRepository(ABC):
    @abstractmethod
    async def add_message(self, message: ChatMessage) -> ChatMessage:
        pass

    @abstractmethod
    async def get_history(self, image_id: str, user_id: str, limit: int = 50) -> List[ChatMessage]:
        pass


