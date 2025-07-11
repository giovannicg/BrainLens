from typing import Optional
from domain.entities.User import User
from domain.repositories.UserRepository import UserRepository
from adapters.dtos.auth_dto import UserRegisterRequest, UserResponse
import logging

logger = logging.getLogger(__name__)

class RegisterUser:
    """Caso de uso para registro de usuarios"""
    
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository
    
    async def execute(self, request: UserRegisterRequest) -> Optional[UserResponse]:
        """Ejecuta el registro de un nuevo usuario"""
        try:
            # Verificar que el email no esté registrado
            existing_user = await self.user_repository.get_by_email(request.email)
            if existing_user:
                logger.warning(f"Intento de registro con email existente: {request.email}")
                raise ValueError("El email ya está registrado")
            
            # Verificar que el username no esté en uso
            existing_username = await self.user_repository.get_by_username(request.username)
            if existing_username:
                logger.warning(f"Intento de registro con username existente: {request.username}")
                raise ValueError("El username ya está en uso")
            
            # Validar contraseña
            if not User.validate_password(request.password):
                raise ValueError("La contraseña no cumple con los requisitos de seguridad")
            
            # Crear hash de la contraseña
            password_hash = User.hash_password(request.password)
            
            # Crear el usuario
            user = User(
                email=request.email,
                username=request.username,
                password_hash=password_hash,
                is_active=True,
                is_verified=False,
                role="user"
            )
            
            # Guardar en la base de datos
            created_user = await self.user_repository.create(user)
            
            logger.info(f"Usuario registrado exitosamente: {created_user.email}")
            
            # Retornar respuesta sin información sensible
            return UserResponse(
                id=created_user.id,
                email=created_user.email,
                username=created_user.username,
                is_active=created_user.is_active,
                is_verified=created_user.is_verified,
                role=created_user.role,
                created_at=created_user.created_at,
                last_login=created_user.last_login
            )
            
        except ValueError as e:
            logger.error(f"Error de validación en registro: {e}")
            raise
        except Exception as e:
            logger.error(f"Error inesperado en registro: {e}")
            raise Exception("Error interno del servidor")
