import os
import uuid
import aiofiles
from datetime import datetime
from typing import Optional, Tuple
from PIL import Image as PILImage
import io
from dotenv import load_dotenv
import boto3
from botocore.client import Config as BotoConfig

load_dotenv()

class StorageService:
    def __init__(self):
        self.storage_type = os.getenv("STORAGE_TYPE", "local")
        self.local_storage_path = os.getenv("LOCAL_STORAGE_PATH", "./storage")
        # S3
        self.s3_bucket = os.getenv("S3_BUCKET", "")
        self.s3_prefix = os.getenv("S3_PREFIX", "").strip()
        if self.s3_prefix and not self.s3_prefix.endswith("/"):
            self.s3_prefix += "/"
        if self.storage_type == "s3":
            self.s3_client = boto3.client(
                "s3",
                region_name=os.getenv("AWS_REGION", os.getenv("AWS_DEFAULT_REGION", None)),
                config=BotoConfig(signature_version="s3v4")
            )
        self._ensure_storage_directory()
    
    def _ensure_storage_directory(self):
        """Asegurar que el directorio de almacenamiento existe"""
        if self.storage_type == "local":
            os.makedirs(self.local_storage_path, exist_ok=True)
            os.makedirs(os.path.join(self.local_storage_path, "images"), exist_ok=True)
            os.makedirs(os.path.join(self.local_storage_path, "staging"), exist_ok=True)
    
    async def save_image(self, file_content: bytes, original_filename: str, user_id: str) -> Tuple[str, dict]:
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"[STORAGE] Guardando imagen para user_id={user_id}, original_filename={original_filename}")
        """Guardar una imagen y retornar información del archivo"""
        # Generar nombre único para el archivo
        file_extension = os.path.splitext(original_filename)[1].lower()
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        logger.info(f"[STORAGE] Nombre único generado: {unique_filename}")

        if self.storage_type == "s3":
            key = f"{self.s3_prefix}images/{user_id}/{unique_filename}"
            content_type = self._get_mime_type(file_extension)
            self.s3_client.put_object(
                Bucket=self.s3_bucket,
                Key=key,
                Body=file_content,
                ContentType=content_type
            )
            file_path = f"s3://{self.s3_bucket}/{key}"
            logger.info(f"[STORAGE] Archivo subido a S3: {file_path}")
        else:
            # Crear directorio para el usuario si no existe
            user_dir = os.path.join(self.local_storage_path, "images", user_id)
            os.makedirs(user_dir, exist_ok=True)
            logger.info(f"[STORAGE] Directorio de usuario asegurado: {user_dir}")

            # Ruta completa del archivo
            file_path = os.path.join(user_dir, unique_filename)
            logger.info(f"[STORAGE] Ruta completa del archivo: {file_path}")

            # Guardar archivo
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(file_content)
            logger.info(f"[STORAGE] Archivo guardado en disco: {file_path}")

        # Obtener información del archivo
        file_size = len(file_content)
        mime_type = self._get_mime_type(file_extension)
        logger.info(f"[STORAGE] Tamaño: {file_size}, MIME: {mime_type}")

        # Obtener dimensiones de la imagen
        width, height = await self._get_image_dimensions(file_content)
        logger.info(f"[STORAGE] Dimensiones: width={width}, height={height}")

        # Crear metadata
        metadata = {
            "original_filename": original_filename,
            "file_extension": file_extension,
            "upload_timestamp": datetime.utcnow().isoformat(),
            "width": width,
            "height": height
        }
        logger.info(f"[STORAGE] Metadata creada: {metadata}")

        return unique_filename, {
            "file_path": file_path,
            "file_size": file_size,
            "mime_type": mime_type,
            "width": width,
            "height": height,
            "metadata": {
                **metadata,
                **({"s3_bucket": self.s3_bucket} if self.storage_type == "s3" else {}),
                **({"s3_prefix": self.s3_prefix} if self.storage_type == "s3" else {}),
            }
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
            if self.storage_type == "s3" and file_path.startswith("s3://"):
                _, rest = file_path.split("s3://", 1)
                bucket, key = rest.split("/", 1)
                self.s3_client.delete_object(Bucket=bucket, Key=key)
                return True
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception:
            return False
    
    async def get_image_path(self, filename: str, user_id: str) -> str:
        """Obtener la ruta completa de una imagen"""
        if self.storage_type == "s3":
            key = f"{self.s3_prefix}images/{user_id}/{filename}"
            return f"s3://{self.s3_bucket}/{key}"
        return os.path.join(self.local_storage_path, "images", user_id, filename)

    def generate_presigned_url(self, file_path: str, expires_in: int = 3600) -> Optional[str]:
        """Generar URL prefirmada para descarga cuando STORAGE_TYPE=s3"""
        try:
            if self.storage_type != "s3" or not file_path.startswith("s3://"):
                return None
            _, rest = file_path.split("s3://", 1)
            bucket, key = rest.split("/", 1)
            return self.s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": bucket, "Key": key},
                ExpiresIn=expires_in
            )
        except Exception:
            return None
    
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
