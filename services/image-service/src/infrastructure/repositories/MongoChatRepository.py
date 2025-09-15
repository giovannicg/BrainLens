from typing import List
from bson import ObjectId
from domain.entities.ChatMessage import ChatMessage
from domain.repositories.ChatRepository import ChatRepository
from infrastructure.database import database


class MongoChatRepository(ChatRepository):
    def __init__(self):
        self.collection = database.get_collection("image_chats")

    async def add_message(self, message: ChatMessage) -> ChatMessage:
        doc = message.model_dump(by_alias=True)
        if doc.get("_id") is None:
            doc["_id"] = ObjectId()
        result = await self.collection.insert_one(doc)
        message.id = str(result.inserted_id)
        return message

    async def get_history(self, image_id: str, user_id: str, limit: int = 50) -> List[ChatMessage]:
        cursor = (
            self.collection.find({"image_id": image_id, "user_id": user_id})
            .sort("timestamp", 1)
            .limit(limit)
        )
        history: List[ChatMessage] = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            history.append(ChatMessage.model_validate(doc))
        return history


