from domain.repositories.AnnotationRepository import AnnotationRepository

class DeleteAnnotationUseCase:
    def __init__(self, annotation_repository: AnnotationRepository):
        self.annotation_repository = annotation_repository
    
    async def execute(self, annotation_id: str) -> bool:
        """Ejecutar el caso de uso de eliminar anotación"""
        try:
            # Verificar que la anotación existe
            existing_annotation = await self.annotation_repository.find_by_id(annotation_id)
            if not existing_annotation:
                raise ValueError("Anotación no encontrada")
            
            # Eliminar del repositorio
            deleted = await self.annotation_repository.delete(annotation_id)
            
            return deleted
            
        except Exception as e:
            raise ValueError(f"Error al eliminar anotación: {str(e)}") 