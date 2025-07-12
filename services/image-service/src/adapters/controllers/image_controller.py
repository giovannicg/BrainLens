from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Query
from fastapi.responses import FileResponse
from typing import List, Optional
import os

from ...usecases.upload_image import UploadImageUseCase
from ...usecases.get_images import GetImagesUseCase, GetImageByIdUseCase, GetImagesByStatusUseCase
from ...usecases.delete_image import DeleteImageUseCase
from ...infrastructure.repositories.MongoImageRepository import MongoImageRepository
from ..dtos.image_dto import ImageResponse, ImageUploadResponse, ImageListResponse, ImageDeleteResponse, ErrorResponse

router = APIRouter(prefix="/images", tags=["images"])

# Inyección de dependencias
def get_image_repository():
    return MongoImageRepository()

def get_upload_use_case(repo: MongoImageRepository = Depends(get_image_repository)):
    return UploadImageUseCase(repo)

def get_get_images_use_case(repo: MongoImageRepository = Depends(get_image_repository)):
    return GetImagesUseCase(repo)

def get_get_image_by_id_use_case(repo: MongoImageRepository = Depends(get_image_repository)):
    return GetImageByIdUseCase(repo)

def get_get_images_by_status_use_case(repo: MongoImageRepository = Depends(get_image_repository)):
    return GetImagesByStatusUseCase(repo)

def get_delete_image_use_case(repo: MongoImageRepository = Depends(get_image_repository)):
    return DeleteImageUseCase(repo)

@router.post("/upload", response_model=ImageUploadResponse)
async def upload_image(
    file: UploadFile = File(...),
    user_id: str = Query(..., description="ID del usuario que sube la imagen"),
    upload_use_case: UploadImageUseCase = Depends(get_upload_use_case)
):
    """Subir una nueva imagen"""
    try:
        # Leer contenido del archivo
        file_content = await file.read()
        
        # Ejecutar caso de uso
        image = await upload_use_case.execute(file_content, file.filename, user_id)
        
        # Convertir a DTO de respuesta
        image_response = ImageResponse(
            id=str(image.id),
            filename=image.filename,
            original_filename=image.original_filename,
            file_size=image.file_size,
            mime_type=image.mime_type,
            width=image.width,
            height=image.height,
            user_id=image.user_id,
            upload_date=image.upload_date,
            processing_status=image.processing_status,
            metadata=image.metadata
        )
        
        return ImageUploadResponse(
            message="Imagen subida exitosamente",
            image=image_response
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")

@router.get("/", response_model=ImageListResponse)
async def get_images(
    user_id: Optional[str] = Query(None, description="Filtrar por ID de usuario"),
    skip: int = Query(0, ge=0, description="Número de registros a saltar"),
    limit: int = Query(100, ge=1, le=1000, description="Número máximo de registros"),
    get_images_use_case: GetImagesUseCase = Depends(get_get_images_use_case)
):
    """Obtener lista de imágenes"""
    try:
        images = await get_images_use_case.execute(user_id=user_id, skip=skip, limit=limit)
        
        # Convertir a DTOs de respuesta
        image_responses = []
        for image in images:
            image_response = ImageResponse(
                id=str(image.id),
                filename=image.filename,
                original_filename=image.original_filename,
                file_size=image.file_size,
                mime_type=image.mime_type,
                width=image.width,
                height=image.height,
                user_id=image.user_id,
                upload_date=image.upload_date,
                processing_status=image.processing_status,
                metadata=image.metadata
            )
            image_responses.append(image_response)
        
        return ImageListResponse(
            images=image_responses,
            total=len(image_responses),
            skip=skip,
            limit=limit
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")

@router.get("/{image_id}", response_model=ImageResponse)
async def get_image(
    image_id: str,
    get_image_use_case: GetImageByIdUseCase = Depends(get_get_image_by_id_use_case)
):
    """Obtener una imagen específica por ID"""
    try:
        image = await get_image_use_case.execute(image_id)
        
        return ImageResponse(
            id=str(image.id),
            filename=image.filename,
            original_filename=image.original_filename,
            file_size=image.file_size,
            mime_type=image.mime_type,
            width=image.width,
            height=image.height,
            user_id=image.user_id,
            upload_date=image.upload_date,
            processing_status=image.processing_status,
            metadata=image.metadata
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")

@router.get("/status/{status}", response_model=ImageListResponse)
async def get_images_by_status(
    status: str,
    get_images_by_status_use_case: GetImagesByStatusUseCase = Depends(get_get_images_by_status_use_case)
):
    """Obtener imágenes por estado de procesamiento"""
    try:
        images = await get_images_by_status_use_case.execute(status)
        
        # Convertir a DTOs de respuesta
        image_responses = []
        for image in images:
            image_response = ImageResponse(
                id=str(image.id),
                filename=image.filename,
                original_filename=image.original_filename,
                file_size=image.file_size,
                mime_type=image.mime_type,
                width=image.width,
                height=image.height,
                user_id=image.user_id,
                upload_date=image.upload_date,
                processing_status=image.processing_status,
                metadata=image.metadata
            )
            image_responses.append(image_response)
        
        return ImageListResponse(
            images=image_responses,
            total=len(image_responses),
            skip=0,
            limit=len(image_responses)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")

@router.delete("/{image_id}", response_model=ImageDeleteResponse)
async def delete_image(
    image_id: str,
    delete_image_use_case: DeleteImageUseCase = Depends(get_delete_image_use_case)
):
    """Eliminar una imagen"""
    try:
        deleted = await delete_image_use_case.execute(image_id)
        
        if deleted:
            return ImageDeleteResponse(
                message="Imagen eliminada exitosamente",
                deleted=True
            )
        else:
            raise HTTPException(status_code=404, detail="Imagen no encontrada")
            
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")

@router.get("/download/{image_id}")
async def download_image(
    image_id: str,
    get_image_use_case: GetImageByIdUseCase = Depends(get_get_image_by_id_use_case)
):
    """Descargar una imagen"""
    try:
        image = await get_image_use_case.execute(image_id)
        
        if not os.path.exists(image.file_path):
            raise HTTPException(status_code=404, detail="Archivo no encontrado en el servidor")
        
        return FileResponse(
            path=image.file_path,
            filename=image.original_filename,
            media_type=image.mime_type
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")
