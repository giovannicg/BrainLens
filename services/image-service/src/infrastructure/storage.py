import os
import uuid
import aiofiles
from datetime import datetime
from typing import Optional, Tuple
from PIL import Image as PILImage
import io
from dotenv import load_dotenv

load_dotenv()

class StorageService:
    def __init__(self):
        self.storage_type = os.getenv("STORAGE_TYPE", "local")
        self.local_storage_path = os.getenv("LOCAL_STORAGE_PATH", "./storage")
        self._ensure_storage_directory()
    
    def _ensure_storage_directory(self):
        """Asegurar que el directorio de almacenamiento existe"""
        if self.storage_type == "local":
            os.makedirs(self.local_storage_path, exist_ok=True)
            os.makedirs(os.path.join(self.local_storage_path, "images"), exist_ok=True)
            os.makedirs(os.path.join(self.local_storage_path, "staging"), exist_ok=True)
    
    async def save_image(self, file_content: bytes, original_filename: str, user_id: str) -> Tuple[str, dict]:
        """Guardar una imagen y retornar información del archivo"""
        # Generar nombre único para el archivo
        file_extension = os.path.splitext(original_filename)[1].lower()
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        
        # Crear directorio para el usuario si no existe
        user_dir = os.path.join(self.local_storage_path, "images", user_id)
        os.makedirs(user_dir, exist_ok=True)
        
        # Ruta completa del archivo
        file_path = os.path.join(user_dir, unique_filename)
        
        # Guardar archivo
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(file_content)
        
        # Obtener información del archivo
        file_size = len(file_content)
        mime_type = self._get_mime_type(file_extension)
        
        # Obtener dimensiones de la imagen
        width, height = await self._get_image_dimensions(file_content)
        
        # Crear metadata
        metadata = {
            "original_filename": original_filename,
            "file_extension": file_extension,
            "upload_timestamp": datetime.utcnow().isoformat(),
            "width": width,
            "height": height
        }
        
        return unique_filename, {
            "file_path": file_path,
            "file_size": file_size,
            "mime_type": mime_type,
            "width": width,
            "height": height,
            "metadata": metadata
        }
    
    async def _get_image_dimensions(self, file_content: bytes) -> Tuple[Optional[int], Optional[int]]:
        """Obtener dimensiones de la imagen"""
        try:
            image = PILImage.open(io.BytesIO(file_content))
            return image.size
        except Exception:
            return None, None
    
    def _get_mime_type(self, file_extension: str) -> str:
        """Obtener el tipo MIME basado en la extensión del archivo"""
        mime_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.bmp': 'image/bmp',
            '.tiff': 'image/tiff',
            '.dcm': 'application/dicom'
        }
        return mime_types.get(file_extension.lower(), 'application/octet-stream')
    
    async def delete_image(self, file_path: str) -> bool:
        """Eliminar una imagen del almacenamiento"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception:
            return False
    
    async def get_image_path(self, filename: str, user_id: str) -> str:
        """Obtener la ruta completa de una imagen"""
        return os.path.join(self.local_storage_path, "images", user_id, filename)
    
    def is_valid_image_type(self, filename: str) -> bool:
        """Verificar si el archivo es un tipo de imagen válido"""
        valid_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.dcm'}
        file_extension = os.path.splitext(filename)[1].lower()
        return file_extension in valid_extensions
    
    def get_max_file_size(self) -> int:
        """Obtener el tamaño máximo de archivo permitido (50MB)"""
        return 50 * 1024 * 1024  # 50MB

    async def save_to_staging(self, file_content: bytes, staging_filename: str) -> str:
        """Guardar archivo en staging para validación"""
        # Ruta completa del archivo en staging
        staging_path = os.path.join(self.local_storage_path, "staging", staging_filename)
        
        # Asegurar que el directorio de staging existe
        os.makedirs(os.path.dirname(staging_path), exist_ok=True)
        
        # Guardar archivo
        async with aiofiles.open(staging_path, 'wb') as f:
            await f.write(file_content)
        
        return staging_path

# Instancia global del servicio de almacenamiento
storage_service = StorageService()
