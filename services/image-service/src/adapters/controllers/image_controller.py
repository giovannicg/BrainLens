from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Query, Form
from fastapi.responses import FileResponse
from typing import List, Optional
import os
import logging

from usecases.upload_image import UploadImageUseCase
from usecases.get_images import GetImagesUseCase, GetImageByIdUseCase, GetImagesByStatusUseCase
from usecases.delete_image import DeleteImageUseCase
from usecases.validate_upload import ValidateUploadUseCase
from infrastructure.repositories.MongoImageRepository import MongoImageRepository
from infrastructure.repositories.MongoChatRepository import MongoChatRepository
from infrastructure.storage import StorageService
from infrastructure.medical_image_validator import MedicalImageValidator
from adapters.dtos.image_dto import (
    ImageResponse, ImageUploadResponse, ImageListResponse, ImageDeleteResponse, 
    ErrorResponse, ProcessingStatusResponse, TumorPredictionResult
)
from adapters.dtos.chat_dto import ChatRequest, ChatResponse, ChatHistoryResponse, ChatMessageDTO
from adapters.dtos.validation_dto import ValidationJobResponse, ValidationJobStatusResponse
from usecases.chat_about_image import ChatAboutImageUseCase
from adapters.gateways.vlm_gateway import VisionLanguageGateway

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/images", tags=["images"])

# Inyección de dependencias
def get_image_repository():
    return MongoImageRepository()

def get_storage_service():
    return StorageService()

def get_medical_validator():
    return MedicalImageValidator()

def get_upload_use_case(
    repo: MongoImageRepository = Depends(get_image_repository),
    storage: StorageService = Depends(get_storage_service)
):
    return UploadImageUseCase(repo, storage)

def get_get_images_use_case(repo: MongoImageRepository = Depends(get_image_repository)):
    return GetImagesUseCase(repo)

def get_get_image_by_id_use_case(repo: MongoImageRepository = Depends(get_image_repository)):
    return GetImageByIdUseCase(repo)

def get_get_images_by_status_use_case(repo: MongoImageRepository = Depends(get_image_repository)):
    return GetImagesByStatusUseCase(repo)

def get_delete_image_use_case(repo: MongoImageRepository = Depends(get_image_repository)):
    return DeleteImageUseCase(repo)

def get_chat_use_case(
    img_repo: MongoImageRepository = Depends(get_image_repository),
    chat_repo: MongoChatRepository = Depends(lambda: MongoChatRepository()),
    vlm: VisionLanguageGateway = Depends(lambda: VisionLanguageGateway()),
):
    return ChatAboutImageUseCase(chat_repo=chat_repo, image_repo=img_repo, vlm=vlm)

def get_validate_upload_use_case():
    return ValidateUploadUseCase(get_storage_service(), get_image_repository())

@router.post("/validate", response_model=dict)
async def validate_medical_image(
    file: UploadFile = File(...),
    medical_validator: MedicalImageValidator = Depends(get_medical_validator)
):
    """Validar si una imagen es una tomografía cerebral válida antes de subirla"""
    try:
        logger.info(f"Validando imagen médica: {file.filename}")
        
        # Leer contenido del archivo
        file_content = await file.read()
        
        if not file_content:
            raise HTTPException(status_code=400, detail="El archivo está vacío")
        
        # Obtener tipo MIME
        import mimetypes
        mime_type, _ = mimetypes.guess_type(file.filename)
        if not mime_type:
            mime_type = "application/octet-stream"
        
        # Validar imagen médica
        is_valid, validation_info = await medical_validator.validate_brain_ct(file_content, mime_type)
        
        return {
            "is_valid": is_valid,
            "filename": file.filename,
            "validation_details": validation_info,
            "message": "Imagen válida para análisis de tumores cerebrales" if is_valid else "La imagen no es una tomografía cerebral válida"
        }
        
    except Exception as e:
        logger.error(f"Error en validación de imagen: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error en validación: {str(e)}")

@router.post("/validate-upload", response_model=ImageUploadResponse)
async def validate_upload(
    file: UploadFile = File(...),
    user_id: str = Form(...),
    custom_filename: Optional[str] = Form(None),
    validate_upload_use_case: ValidateUploadUseCase = Depends(get_validate_upload_use_case)
):
    """Validar médicamente y guardar la imagen de forma síncrona."""
    try:
        logger.info(f"Iniciando validación de upload para archivo: {file.filename}")
        
        # Leer contenido del archivo
        file_content = await file.read()
        
        # Ejecutar validación síncrona y guardar imagen
        result = await validate_upload_use_case.execute(
            file_content=file_content,
            original_filename=file.filename,
            user_id=user_id,
            custom_filename=custom_filename
        )

        image = result.get("image")
        error_code = result.get("error_code")
        error_detail = result.get("error_detail")
        message = result.get("message", "")

        if not image:
            # Error en validación o predicción: devolver mensaje específico
            return ImageUploadResponse(
                message=message or "Error al procesar la imagen",
                image=None,
                processing_status="failed",
                status="failed",
                error_code=error_code,
                error_detail=error_detail,
            )

        return ImageUploadResponse(
            message=message or "Imagen validada y guardada",
            image=ImageResponse(
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
                metadata=image.metadata,
            ),
            processing_status=image.processing_status,
            status="completed"
        )
        
    except Exception as e:
        logger.error(f"Error en validate_upload: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Error en validación: {str(e)}")

# Ruta de compatibilidad antigua eliminada: el flujo ahora es síncrono

@router.post("/upload", response_model=ImageUploadResponse)
async def upload_image(
    file: UploadFile = File(...),
    user_id: str = Form(...),
    custom_filename: Optional[str] = Form(None)
):
    try:
        file_content = await file.read()
        upload_use_case = UploadImageUseCase(get_image_repository(), get_storage_service())
        result = await upload_use_case.execute(
            file_content=file_content,
            original_filename=file.filename,
            user_id=user_id,
            custom_filename=custom_filename
        )
        image = result.get("image")
        if not image:
            raise ValueError("No se pudo subir la imagen")
        return ImageUploadResponse(
            message=result.get("message", "Imagen subida correctamente"),
            image=ImageResponse(
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
                metadata=image.metadata,
            ),
            processing_status=image.processing_status,
            status="completed"
        )
    except Exception as e:
        logger.error(f"[UPLOAD] Error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{image_id}/chat", response_model=ChatHistoryResponse)
async def get_chat_history(
    image_id: str,
    user_id: str = Query(..., description="ID del usuario"),
    limit: int = Query(50, ge=1, le=200),
    chat_use_case: ChatAboutImageUseCase = Depends(get_chat_use_case),
):
    try:
        history = await chat_use_case.get_history(image_id=image_id, user_id=user_id, limit=limit)
        messages = [
            ChatMessageDTO(
                id=m.id,
                image_id=m.image_id,
                user_id=m.user_id,
                role=m.role,
                content=m.content,
                timestamp=m.timestamp,
            )
            for m in history
        ]
        return ChatHistoryResponse(messages=messages, total=len(messages))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo historial: {str(e)}")

@router.post("/{image_id}/chat", response_model=ChatResponse)
async def chat_about_image(
    image_id: str,
    body: ChatRequest,
    user_id: str = Query(..., description="ID del usuario"),
    chat_use_case: ChatAboutImageUseCase = Depends(get_chat_use_case),
):
    try:
        assistant_msg = await chat_use_case.ask(image_id=image_id, user_id=user_id, prompt=body.message)
        msg_dto = ChatMessageDTO(
            id=assistant_msg.id,
            image_id=assistant_msg.image_id,
            user_id=assistant_msg.user_id,
            role=assistant_msg.role,
            content=assistant_msg.content,
            timestamp=assistant_msg.timestamp,
        )
        # opcional: devolver último historial corto
        history = await chat_use_case.get_history(image_id=image_id, user_id=user_id, limit=50)
        history_dto = [
            ChatMessageDTO(
                id=m.id,
                image_id=m.image_id,
                user_id=m.user_id,
                role=m.role,
                content=m.content,
                timestamp=m.timestamp,
            )
            for m in history
        ]
        return ChatResponse(answer=assistant_msg.content, message=msg_dto, history=history_dto)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en chat: {str(e)}")

@router.get("/{image_id}/processing-status", response_model=ProcessingStatusResponse)
async def get_processing_status(
    image_id: str,
    get_image_use_case: GetImageByIdUseCase = Depends(get_get_image_by_id_use_case)
):
    """Obtener el estado del procesamiento de una imagen"""
    try:
        image = await get_image_use_case.execute(image_id)
        
        # Extraer información del procesamiento
        processing_started = None
        processing_completed = None
        prediction = None
        
        if image.metadata:
            if 'processing_started' in image.metadata:
                processing_started = image.metadata['processing_started']
            if 'processing_completed' in image.metadata:
                processing_completed = image.metadata['processing_completed']
            if 'tumor_analysis' in image.metadata:
                tumor_data = image.metadata['tumor_analysis']
                prediction = TumorPredictionResult(
                    es_tumor=tumor_data['es_tumor'],
                    clase_predicha=tumor_data['clase_predicha'],
                    confianza=tumor_data['confianza'],
                    probabilidades=tumor_data['probabilidades'],
                    recomendacion=tumor_data['recomendacion']
                )
        
        # Generar mensaje según el estado
        if image.processing_status == "pending":
            message = "La imagen está en cola para procesamiento"
        elif image.processing_status == "processing":
            message = "La imagen se está procesando actualmente"
        elif image.processing_status == "completed":
            message = "El análisis se ha completado exitosamente"
        elif image.processing_status == "failed":
            error_msg = image.metadata.get('processing_error', 'Error desconocido') if image.metadata else 'Error desconocido'
            message = f"El procesamiento falló: {error_msg}"
        else:
            message = f"Estado desconocido: {image.processing_status}"
        
        return ProcessingStatusResponse(
            image_id=str(image.id),
            status=image.processing_status,
            message=message,
            prediction=prediction,
            processing_started=processing_started,
            processing_completed=processing_completed
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
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
        logger.info(f"Obteniendo imágenes para user_id: {user_id}, skip: {skip}, limit: {limit}")
        
        # Ejecutar de forma asíncrona
        images = await get_images_use_case.execute(user_id=user_id, skip=skip, limit=limit)
        logger.info(f"Imágenes obtenidas: {len(images)}")
        
        # Convertir a DTOs de respuesta de forma eficiente
        image_responses = []
        for i, image in enumerate(images):
            try:
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
            except Exception as img_error:
                logger.error(f"Error convirtiendo imagen {i+1}: {str(img_error)}")
                # Continuar con las siguientes imágenes en lugar de fallar completamente
                continue
        
        logger.info(f"Total de imágenes convertidas: {len(image_responses)}")
        return ImageListResponse(
            images=image_responses,
            total=len(image_responses),
            skip=skip,
            limit=limit
        )
        
    except Exception as e:
        logger.error(f"Error en get_images: {str(e)}")
        logger.error(f"Tipo de error: {type(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
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
            # Log extra y detalle del path
            logger.error(f"Archivo no encontrado: {image.file_path}")
            raise HTTPException(status_code=404, detail=f"Archivo no encontrado en el servidor: {image.file_path}")
        
        return FileResponse(
            path=image.file_path,
            filename=image.original_filename,
            media_type=image.mime_type
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")
