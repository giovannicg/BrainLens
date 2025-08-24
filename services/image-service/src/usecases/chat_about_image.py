from typing import List
from domain.entities.ChatMessage import ChatMessage
from domain.repositories.ChatRepository import ChatRepository
from domain.repositories.ImageRepository import ImageRepository
from adapters.gateways.vlm_gateway import VisionLanguageGateway


class ChatAboutImageUseCase:
    def __init__(self, chat_repo: ChatRepository, image_repo: ImageRepository, vlm: VisionLanguageGateway):
        self.chat_repo = chat_repo
        self.image_repo = image_repo
        self.vlm = vlm

    async def get_history(self, image_id: str, user_id: str, limit: int = 50) -> List[ChatMessage]:
        return await self.chat_repo.get_history(image_id=image_id, user_id=user_id, limit=limit)

    async def ask(self, image_id: str, user_id: str, prompt: str) -> ChatMessage:
        # 1. Cargar imagen
        image = await self.image_repo.find_by_id(image_id)
        if not image:
            raise ValueError("Imagen no encontrada")

        # 2. Guardar mensaje del usuario
        user_msg = ChatMessage(image_id=image_id, user_id=user_id, role="user", content=prompt)
        await self.chat_repo.add_message(user_msg)

        # 3. Leer bytes de imagen
        with open(image.file_path, "rb") as f:
            image_bytes = f.read()

        # 4. Consultar VLM
        answer = self.vlm.ask_about_image(prompt=prompt, image_bytes=image_bytes, mime_type=image.mime_type)

        # 5. Guardar respuesta del asistente
        assistant_msg = ChatMessage(image_id=image_id, user_id=user_id, role="assistant", content=answer)
        await self.chat_repo.add_message(assistant_msg)

        return assistant_msg


