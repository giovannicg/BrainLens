import os
from azure.storage.file import FileService
from azure.storage.file.models import File
from typing import Optional, BinaryIO
from pathlib import Path
import logging
import io

logger = logging.getLogger(__name__)

class StorageService:
    """Servicio de almacenamiento que soporta Azure Files y filesystem local"""
    
    def __init__(self, storage_type: str = "local"):
        self.storage_type = storage_type
        
        if storage_type == "azure":
            # Configuración para Azure Files
            account_name = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
            account_key = os.getenv("AZURE_STORAGE_ACCOUNT_KEY")
            self.share_name = os.getenv("AZURE_FILE_SHARE_NAME", "brainlens-files")
            
            if not account_name or not account_key:
                raise ValueError("AZURE_STORAGE_ACCOUNT_NAME y AZURE_STORAGE_ACCOUNT_KEY son requeridos para Azure Files")
            
            self.file_service = FileService(account_name=account_name, account_key=account_key)
            
            # Crear el share si no existe
            if not self.file_service.exists(self.share_name):
                self.file_service.create_share(self.share_name)
                logger.info(f"Share '{self.share_name}' creado en Azure Files")
        else:
            # Configuración para almacenamiento local
            self.local_storage_path = Path(os.getenv("LOCAL_STORAGE_PATH", "./storage"))
            self.local_storage_path.mkdir(exist_ok=True)
    
    def upload_file(self, file_path: str, file_content: BinaryIO, content_type: str = None) -> str:
        """Sube un archivo al almacenamiento"""
        if self.storage_type == "azure":
            return self._upload_to_azure(file_path, file_content, content_type)
        else:
            return self._upload_to_local(file_path, file_content)
    
    def download_file(self, file_path: str) -> Optional[bytes]:
        """Descarga un archivo del almacenamiento"""
        if self.storage_type == "azure":
            return self._download_from_azure(file_path)
        else:
            return self._download_from_local(file_path)
    
    def delete_file(self, file_path: str) -> bool:
        """Elimina un archivo del almacenamiento"""
        if self.storage_type == "azure":
            return self._delete_from_azure(file_path)
        else:
            return self._delete_from_local(file_path)
    
    def _upload_to_azure(self, file_path: str, file_content: BinaryIO, content_type: str = None) -> str:
        """Sube archivo a Azure Files"""
        try:
            # Crear directorio si no existe
            directory_path = os.path.dirname(file_path)
            if directory_path and not self.file_service.exists(self.share_name, directory_path):
                self.file_service.create_directory(self.share_name, directory_path)
            
            # Subir archivo
            file_content.seek(0)  # Resetear posición del archivo
            self.file_service.create_file_from_stream(
                share_name=self.share_name,
                directory_name=os.path.dirname(file_path) or None,
                file_name=os.path.basename(file_path),
                stream=file_content,
                count=len(file_content.read()),
                content_settings=None
            )
            
            return f"azure://{self.share_name}/{file_path}"
        except Exception as e:
            logger.error(f"Error uploading to Azure Files: {e}")
            raise
    
    def _upload_to_local(self, file_path: str, file_content: BinaryIO) -> str:
        """Sube archivo al almacenamiento local"""
        try:
            full_path = self.local_storage_path / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(full_path, 'wb') as f:
                f.write(file_content.read())
            
            return str(full_path)
        except Exception as e:
            logger.error(f"Error uploading to local storage: {e}")
            raise
    
    def _download_from_azure(self, file_path: str) -> Optional[bytes]:
        """Descarga archivo de Azure Files"""
        try:
            file_stream = self.file_service.get_file_to_stream(
                share_name=self.share_name,
                directory_name=os.path.dirname(file_path) or None,
                file_name=os.path.basename(file_path),
                stream=io.BytesIO()
            )
            return file_stream.content
        except Exception as e:
            logger.error(f"Error downloading from Azure Files: {e}")
            return None
    
    def _download_from_local(self, file_path: str) -> Optional[bytes]:
        """Descarga archivo del almacenamiento local"""
        try:
            full_path = self.local_storage_path / file_path
            if full_path.exists():
                return full_path.read_bytes()
            return None
        except Exception as e:
            logger.error(f"Error downloading from local storage: {e}")
            return None
    
    def _delete_from_azure(self, file_path: str) -> bool:
        """Elimina archivo de Azure Files"""
        try:
            self.file_service.delete_file(
                share_name=self.share_name,
                directory_name=os.path.dirname(file_path) or None,
                file_name=os.path.basename(file_path)
            )
            return True
        except Exception as e:
            logger.error(f"Error deleting from Azure Files: {e}")
            return False
    
    def _delete_from_local(self, file_path: str) -> bool:
        """Elimina archivo del almacenamiento local"""
        try:
            full_path = self.local_storage_path / file_path
            if full_path.exists():
                full_path.unlink()
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting from local storage: {e}")
            return False

# Instancia global del servicio de almacenamiento
storage_service = StorageService(os.getenv("STORAGE_TYPE", "local")) 