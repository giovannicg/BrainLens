from typing import Optional
from ...domain.entities.Annotation import Annotation, AnnotationShape, AnnotationPoint
from ...domain.repositories.AnnotationRepository import AnnotationRepository

class CreateAnnotationUseCase:
    def __init__(self, annotation_repository: AnnotationRepository):
        self.annotation_repository = annotation_repository
    
    async def execute(self, annotation_data: dict, user_id: str) -> Annotation:
        """Ejecutar el caso de uso de crear anotación"""
        try:
            # Convertir shapes de la request a entidades
            shapes = []
            for shape_data in annotation_data.get("shapes", []):
                points = [AnnotationPoint(x=p["x"], y=p["y"]) for p in shape_data["points"]]
                shape = AnnotationShape(
                    type=shape_data["type"],
                    points=points,
                    properties=shape_data.get("properties", {})
                )
                shapes.append(shape)
            
            # Crear entidad Annotation
            annotation = Annotation(
                image_id=annotation_data["image_id"],
                user_id=user_id,
                title=annotation_data["title"],
                description=annotation_data["description"],
                category=annotation_data["category"],
                confidence=annotation_data.get("confidence", 1.0),
                shapes=shapes,
                metadata=annotation_data.get("metadata", {}),
                status="pending"
            )
            
            # Guardar en repositorio
            saved_annotation = await self.annotation_repository.save(annotation)
            
            return saved_annotation
            
        except Exception as e:
            raise ValueError(f"Error al crear anotación: {str(e)}")
