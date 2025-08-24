import os
from typing import List
from dotenv import load_dotenv
import requests

load_dotenv()


class VisionLanguageGateway:
    def __init__(self):
        # Proveedor: 'ollama' (por defecto) u 'openai'
        self.provider = os.getenv("VLM_PROVIDER", "ollama").lower()
        self.model = os.getenv("VLM_MODEL", "llama3.2-vision")
        self.system_prompt = os.getenv(
            "VLM_SYSTEM_PROMPT",
            "Responde SIEMPRE en español de forma clara, concisa y clínica cuando corresponda.",
        )
        # OpenAI
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.api_base = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        # Ollama
        self.ollama_base = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.force_spanish = os.getenv("VLM_FORCE_SPANISH", "true").lower() == "true"

    def build_openai_headers(self):
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def ask_about_image(self, prompt: str, image_bytes: bytes, mime_type: str) -> str:
        import base64

        image_b64 = base64.b64encode(image_bytes).decode("utf-8")
        # Reforzar idioma en el propio contenido del usuario
        wrapped_prompt = (
            f"{self.system_prompt}\n\n" if self.system_prompt else ""
        ) + f"Responde únicamente en español. Pregunta del usuario: {prompt}"

        if self.provider == "ollama":
            # Ollama: chat multimodal con modelos como llama3.2-vision
            url = f"{self.ollama_base}/api/chat"
            messages = []
            if self.system_prompt:
                messages.append({"role": "system", "content": self.system_prompt})
            messages.append({
                "role": "user",
                "content": wrapped_prompt,
                "images": [image_b64],
            })
            payload = {"model": self.model, "messages": messages, "stream": False}
            resp = requests.post(url, json=payload, timeout=120)
            resp.raise_for_status()
            data = resp.json()
            # Estructura típica: { message: { role, content }, done: true, ... }
            if "message" in data and isinstance(data["message"], dict):
                answer_text = str(data["message"].get("content", "")).strip()
                if self.force_spanish and answer_text:
                    # Traducción post-proceso al español usando el mismo modelo
                    gen_url = f"{self.ollama_base}/api/generate"
                    gen_payload = {
                        "model": self.model,
                        "prompt": f"Traduce al español, tono clínico y conciso, el siguiente texto:\n'''{answer_text}'''",
                        "stream": False,
                    }
                    try:
                        gen_resp = requests.post(gen_url, json=gen_payload, timeout=60)
                        gen_resp.raise_for_status()
                        gen_data = gen_resp.json()
                        translated = gen_data.get("response", "").strip()
                        if translated:
                            return translated
                    except Exception:
                        pass
                return answer_text
            # v0.1.43+ puede devolver una lista de mensajes en stream desactivado
            if "messages" in data and isinstance(data["messages"], list) and data["messages"]:
                answer_text = str(data["messages"][-1].get("content", "")).strip()
                if self.force_spanish and answer_text:
                    gen_url = f"{self.ollama_base}/api/generate"
                    gen_payload = {
                        "model": self.model,
                        "prompt": f"Traduce al español, tono clínico y conciso, el siguiente texto:\n'''{answer_text}'''",
                        "stream": False,
                    }
                    try:
                        gen_resp = requests.post(gen_url, json=gen_payload, timeout=60)
                        gen_resp.raise_for_status()
                        gen_data = gen_resp.json()
                        translated = gen_data.get("response", "").strip()
                        if translated:
                            return translated
                    except Exception:
                        pass
                return answer_text
            return ""

        if self.provider == "openai":
            # Usa el endpoint de chat multimodal de OpenAI (vision) con base64 en data URI
            url = f"{self.api_base}/chat/completions"
            messages = []
            if self.system_prompt:
                messages.append({"role": "system", "content": self.system_prompt})
            messages.append({
                "role": "user",
                "content": [
                    {"type": "text", "text": wrapped_prompt},
                    {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{image_b64}"}},
                ],
            })
            payload = {"model": self.model, "messages": messages}
            resp = requests.post(url, headers=self.build_openai_headers(), json=payload, timeout=60)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"].strip()

        raise NotImplementedError(f"Proveedor VLM no soportado: {self.provider}")


