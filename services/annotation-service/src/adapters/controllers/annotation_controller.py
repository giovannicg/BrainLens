from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from datetime import datetime

from usecases.create_annotation import CreateAnnotationUseCase
from usecases.get_annotations import (
    GetAnnotationsUseCase, GetAnnotationByIdUseCase, 
    GetAnnotationsByStatusUseCase, GetAnnotationsByCategoryUseCase,
    GetPendingReviewsUseCase
)
from usecases.update_annotation import UpdateAnnotationUseCase, ReviewAnnotationUseCase
from usecases.delete_annotation import DeleteAnnotationUseCase
from infrastructure.repositories.MongoAnnotationRepository import MongoAnnotationRepository
from adapters.gateways.annotation_gateway import AnnotationGateway
from adapters.dtos.annotation_dto import (
    AnnotationResponse, CreateAnnotationRequest, UpdateAnnotationRequest,
    ReviewAnnotationRequest, AnnotationListResponse, AnnotationCreateResponse,
    AnnotationUpdateResponse, AnnotationDeleteResponse, ErrorResponse
)
from infrastructure.database import database

router = APIRouter(prefix="/annotations", tags=["annotations"])

# Inyección de dependencias
def get_annotation_repository():
    return AnnotationGateway()

def get_create_use_case(repo: AnnotationGateway = Depends(get_annotation_repository)):
    return CreateAnnotationUseCase(repo)

def get_get_annotations_use_case(repo: AnnotationGateway = Depends(get_annotation_repository)):
    return GetAnnotationsUseCase(repo)

def get_get_annotation_by_id_use_case(repo: AnnotationGateway = Depends(get_annotation_repository)):
    return GetAnnotationByIdUseCase(repo)

def get_get_annotations_by_status_use_case(repo: AnnotationGateway = Depends(get_annotation_repository)):
    return GetAnnotationsByStatusUseCase(repo)

def get_get_annotations_by_category_use_case(repo: AnnotationGateway = Depends(get_annotation_repository)):
    return GetAnnotationsByCategoryUseCase(repo)

def get_get_pending_reviews_use_case(repo: AnnotationGateway = Depends(get_annotation_repository)):
    return GetPendingReviewsUseCase(repo)

def get_update_annotation_use_case(repo: AnnotationGateway = Depends(get_annotation_repository)):
    return UpdateAnnotationUseCase(repo)

def get_review_annotation_use_case(repo: AnnotationGateway = Depends(get_annotation_repository)):
    return ReviewAnnotationUseCase(repo)

def get_delete_annotation_use_case(repo: AnnotationGateway = Depends(get_annotation_repository)):
    return DeleteAnnotationUseCase(repo)

def _annotation_to_response(annotation) -> AnnotationResponse:
    """Convertir entidad Annotation a DTO de respuesta"""
    return AnnotationResponse(
        id=str(annotation.id),
        image_id=annotation.image_id,
        user_id=annotation.user_id,
        title=annotation.title,
        description=annotation.description,
        category=annotation.category,
        confidence=annotation.confidence,
        status=annotation.status,
        shapes=[
            {
                "type": shape.type,
                "points": [{"x": p.x, "y": p.y} for p in shape.points],
                "properties": shape.properties
            }
            for shape in annotation.shapes
        ],
        metadata=annotation.metadata,
        created_at=annotation.created_at,
        updated_at=annotation.updated_at,
        reviewed_by=annotation.reviewed_by,
        reviewed_at=annotation.reviewed_at,
        review_notes=annotation.review_notes
    )

@router.post("/", response_model=AnnotationCreateResponse)
async def create_annotation(
    annotation_data: CreateAnnotationRequest,
    user_id: str = Query(..., description="ID del usuario que crea la anotación"),
    create_use_case: CreateAnnotationUseCase = Depends(get_create_use_case)
):
    """Crear una nueva anotación"""
    try:
        # Ejecutar caso de uso
        annotation = await create_use_case.execute(annotation_data.dict(), user_id)
        
        # Convertir a DTO de respuesta
        annotation_response = _annotation_to_response(annotation)
        
        return AnnotationCreateResponse(
            message="Anotación creada exitosamente",
            annotation=annotation_response
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")

@router.get("/", response_model=AnnotationListResponse)
async def get_annotations(
    user_id: Optional[str] = Query(None, description="Filtrar por ID de usuario"),
    image_id: Optional[str] = Query(None, description="Filtrar por ID de imagen"),
    skip: int = Query(0, ge=0, description="Número de registros a saltar"),
    limit: int = Query(100, ge=1, le=1000, description="Número máximo de registros"),
    get_annotations_use_case: GetAnnotationsUseCase = Depends(get_get_annotations_use_case)
):
    """Obtener lista de anotaciones"""
    try:
        annotations = await get_annotations_use_case.execute(
            user_id=user_id, image_id=image_id, skip=skip, limit=limit
        )
        
        # Convertir a DTOs de respuesta
        annotation_responses = [_annotation_to_response(ann) for ann in annotations]
        
        return AnnotationListResponse(
            annotations=annotation_responses,
            total=len(annotation_responses),
            skip=skip,
            limit=limit
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")

@router.get("/{annotation_id}", response_model=AnnotationResponse)
async def get_annotation(
    annotation_id: str,
    get_annotation_use_case: GetAnnotationByIdUseCase = Depends(get_get_annotation_by_id_use_case)
):
    """Obtener una anotación específica por ID"""
    try:
        annotation = await get_annotation_use_case.execute(annotation_id)
        return _annotation_to_response(annotation)
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")

@router.get("/status/{status}", response_model=AnnotationListResponse)
async def get_annotations_by_status(
    status: str,
    get_annotations_by_status_use_case: GetAnnotationsByStatusUseCase = Depends(get_get_annotations_by_status_use_case)
):
    """Obtener anotaciones por estado"""
    try:
        annotations = await get_annotations_by_status_use_case.execute(status)
        annotation_responses = [_annotation_to_response(ann) for ann in annotations]
        
        return AnnotationListResponse(
            annotations=annotation_responses,
            total=len(annotation_responses),
            skip=0,
            limit=len(annotation_responses)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")

@router.get("/category/{category}", response_model=AnnotationListResponse)
async def get_annotations_by_category(
    category: str,
    get_annotations_by_category_use_case: GetAnnotationsByCategoryUseCase = Depends(get_get_annotations_by_category_use_case)
):
    """Obtener anotaciones por categoría"""
    try:
        annotations = await get_annotations_by_category_use_case.execute(category)
        annotation_responses = [_annotation_to_response(ann) for ann in annotations]
        
        return AnnotationListResponse(
            annotations=annotation_responses,
            total=len(annotation_responses),
            skip=0,
            limit=len(annotation_responses)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")

@router.get("/pending/reviews", response_model=AnnotationListResponse)
async def get_pending_reviews(
    get_pending_reviews_use_case: GetPendingReviewsUseCase = Depends(get_get_pending_reviews_use_case)
):
    """Obtener anotaciones pendientes de revisión"""
    try:
        annotations = await get_pending_reviews_use_case.execute()
        annotation_responses = [_annotation_to_response(ann) for ann in annotations]
        
        return AnnotationListResponse(
            annotations=annotation_responses,
            total=len(annotation_responses),
            skip=0,
            limit=len(annotation_responses)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")

@router.put("/{annotation_id}", response_model=AnnotationUpdateResponse)
async def update_annotation(
    annotation_id: str,
    update_data: UpdateAnnotationRequest,
    update_annotation_use_case: UpdateAnnotationUseCase = Depends(get_update_annotation_use_case)
):
    """Actualizar una anotación"""
    try:
        # Filtrar campos no nulos
        update_dict = {k: v for k, v in update_data.dict().items() if v is not None}
        
        if not update_dict:
            raise ValueError("No se proporcionaron datos para actualizar")
        
        updated_annotation = await update_annotation_use_case.execute(annotation_id, update_dict)
        
        if not updated_annotation:
            raise HTTPException(status_code=404, detail="Anotación no encontrada")
        
        annotation_response = _annotation_to_response(updated_annotation)
        
        return AnnotationUpdateResponse(
            message="Anotación actualizada exitosamente",
            annotation=annotation_response
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")

@router.post("/{annotation_id}/review", response_model=AnnotationUpdateResponse)
async def review_annotation(
    annotation_id: str,
    review_data: ReviewAnnotationRequest,
    reviewer_id: str = Query(..., description="ID del revisor"),
    review_annotation_use_case: ReviewAnnotationUseCase = Depends(get_review_annotation_use_case)
):
    """Revisar una anotación"""
    try:
        updated_annotation = await review_annotation_use_case.execute(
            annotation_id, review_data.dict(), reviewer_id
        )
        
        if not updated_annotation:
            raise HTTPException(status_code=404, detail="Anotación no encontrada")
        
        annotation_response = _annotation_to_response(updated_annotation)
        
        return AnnotationUpdateResponse(
            message="Anotación revisada exitosamente",
            annotation=annotation_response
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")

@router.delete("/{annotation_id}", response_model=AnnotationDeleteResponse)
async def delete_annotation(
    annotation_id: str,
    delete_annotation_use_case: DeleteAnnotationUseCase = Depends(get_delete_annotation_use_case)
):
    """Eliminar una anotación"""
    try:
        deleted = await delete_annotation_use_case.execute(annotation_id)
        
        if deleted:
            return AnnotationDeleteResponse(
                message="Anotación eliminada exitosamente",
                deleted=True
            )
        else:
            raise HTTPException(status_code=404, detail="Anotación no encontrada")
            
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")
