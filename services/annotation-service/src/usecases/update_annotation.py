from typing import Optional
from datetime import datetime
from domain.entities.Annotation import Annotation, AnnotationShape, AnnotationPoint
from domain.repositories.AnnotationRepository import AnnotationRepository

class UpdateAnnotationUseCase:
    def __init__(self, annotation_repository: AnnotationRepository):
        self.annotation_repository = annotation_repository
    
    async def execute(self, annotation_id: str, update_data: dict) -> Optional[Annotation]:
        """Ejecutar el caso de uso de actualizar anotación"""
        try:
            # Verificar que la anotación existe
            existing_annotation = await self.annotation_repository.find_by_id(annotation_id)
            if not existing_annotation:
                raise ValueError("Anotación no encontrada")
            
            # Procesar shapes si se proporcionan
            if "shapes" in update_data:
                shapes = []
                for shape_data in update_data["shapes"]:
                    points = [AnnotationPoint(x=p["x"], y=p["y"]) for p in shape_data["points"]]
                    shape = AnnotationShape(
                        type=shape_data["type"],
                        points=points,
                        properties=shape_data.get("properties", {})
                    )
                    shapes.append(shape)
                update_data["shapes"] = shapes
            
            # Actualizar en repositorio
            updated_annotation = await self.annotation_repository.update(annotation_id, update_data)
            
            return updated_annotation
            
        except Exception as e:
            raise ValueError(f"Error al actualizar anotación: {str(e)}")

class ReviewAnnotationUseCase:
    def __init__(self, annotation_repository: AnnotationRepository):
        self.annotation_repository = annotation_repository
    
    async def execute(self, annotation_id: str, review_data: dict, reviewer_id: str) -> Optional[Annotation]:
        """Ejecutar el caso de uso de revisar anotación"""
        try:
            # Verificar que la anotación existe
            existing_annotation = await self.annotation_repository.find_by_id(annotation_id)
            if not existing_annotation:
                raise ValueError("Anotación no encontrada")
            
            # Preparar datos de revisión
            review_update = {
                "status": review_data["status"],
                "reviewed_by": reviewer_id,
                "reviewed_at": datetime.utcnow(),
                "review_notes": review_data.get("review_notes")
            }
            
            # Actualizar en repositorio
            updated_annotation = await self.annotation_repository.update(annotation_id, review_update)
            
            return updated_annotation
            
        except Exception as e:
            raise ValueError(f"Error al revisar anotación: {str(e)}") 