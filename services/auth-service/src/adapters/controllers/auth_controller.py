from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from domain.repositories.UserRepository import UserRepository
from adapters.gateways.user_gateway import UserGateway
from usecases.RegisterUser import RegisterUser
from usecases.AuthenticateUser import AuthenticateUser
from adapters.dtos.auth_dto import (
    UserRegisterRequest, UserLoginRequest, UserResponse, 
    TokenResponse, RefreshTokenRequest, ChangePasswordRequest,
    ForgotPasswordRequest, ResetPasswordRequest, VerifyEmailRequest
)
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])
security = HTTPBearer()

# Dependency para obtener el repositorio
def get_user_repository() -> UserRepository:
    return UserGateway()

# Dependency para obtener el usuario actual
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    user_repository: UserRepository = Depends(get_user_repository)
) -> Optional[UserResponse]:
    """Obtiene el usuario actual basado en el token JWT"""
    try:
        authenticate_use_case = AuthenticateUser(user_repository)
        user = await authenticate_use_case.get_current_user(credentials.credentials)
        
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido o expirado",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return UserResponse(
            id=user.id,
            email=user.email,
            username=user.username,
            is_active=user.is_active,
            is_verified=user.is_verified,
            role=user.role,
            created_at=user.created_at,
            last_login=user.last_login
        )
        
    except Exception as e:
        logger.error(f"Error obteniendo usuario actual: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    request: UserRegisterRequest,
    user_repository: UserRepository = Depends(get_user_repository)
):
    """Registra un nuevo usuario"""
    try:
        register_use_case = RegisterUser(user_repository)
        user_response = await register_use_case.execute(request)
        
        return user_response
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error en registro: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )

@router.post("/login", response_model=TokenResponse)
async def login_user(
    request: UserLoginRequest,
    user_repository: UserRepository = Depends(get_user_repository)
):
    """Autentica un usuario y retorna tokens JWT"""
    try:
        authenticate_use_case = AuthenticateUser(user_repository)
        token_response = await authenticate_use_case.execute(request)
        
        return token_response
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error en login: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    user_repository: UserRepository = Depends(get_user_repository)
):
    """Refresca un token de acceso usando un refresh token"""
    try:
        authenticate_use_case = AuthenticateUser(user_repository)
        token_response = await authenticate_use_case.refresh_access_token(request.refresh_token)
        
        return token_response
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error refrescando token: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: UserResponse = Depends(get_current_user)
):
    """Obtiene información del usuario actual"""
    return current_user

@router.post("/change-password")
async def change_password(
    request: ChangePasswordRequest,
    current_user: UserResponse = Depends(get_current_user),
    user_repository: UserRepository = Depends(get_user_repository)
):
    """Cambia la contraseña del usuario actual"""
    try:
        # Obtener usuario completo
        user = await user_repository.get_by_id(current_user.id)
        
        # Verificar contraseña actual
        if not user.verify_password(request.current_password, user.password_hash):
            raise ValueError("Contraseña actual incorrecta")
        
        # Validar nueva contraseña
        if not user.validate_password(request.new_password):
            raise ValueError("La nueva contraseña no cumple con los requisitos de seguridad")
        
        # Actualizar contraseña
        user.password_hash = user.hash_password(request.new_password)
        await user_repository.update(user)
        
        return {"message": "Contraseña cambiada exitosamente"}
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error cambiando contraseña: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )

@router.post("/forgot-password")
async def forgot_password(request: ForgotPasswordRequest):
    """Solicita el reset de contraseña (placeholder)"""
    # TODO: Implementar envío de email con token de reset
    return {"message": "Si el email existe, se enviará un enlace de reset"}

@router.post("/reset-password")
async def reset_password(request: ResetPasswordRequest):
    """Resetea la contraseña usando un token (placeholder)"""
    # TODO: Implementar verificación de token y reset de contraseña
    return {"message": "Contraseña reseteada exitosamente"}

@router.post("/verify-email")
async def verify_email(request: VerifyEmailRequest):
    """Verifica el email del usuario (placeholder)"""
    # TODO: Implementar verificación de email
    return {"message": "Email verificado exitosamente"}

@router.post("/logout")
async def logout():
    """Logout del usuario (invalida refresh token)"""
    # TODO: Implementar blacklist de refresh tokens
    return {"message": "Logout exitoso"}
