from typing import Optional, Tuple
from datetime import datetime, timedelta
import jwt
import os
from domain.entities.User import User
from domain.repositories.UserRepository import UserRepository
from adapters.dtos.auth_dto import UserLoginRequest, TokenResponse, UserResponse
import logging

logger = logging.getLogger(__name__)

class AuthenticateUser:
    """Caso de uso para autenticación de usuarios"""
    
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository
        self.secret_key = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
        self.algorithm = "HS256"
        self.access_token_expire_minutes = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
        self.refresh_token_expire_days = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
    
    async def execute(self, request: UserLoginRequest) -> Optional[TokenResponse]:
        """Ejecuta la autenticación de un usuario"""
        try:
            # Buscar usuario por email
            user = await self.user_repository.get_by_email(request.email)
            if not user:
                logger.warning(f"Intento de login con email inexistente: {request.email}")
                raise ValueError("Credenciales inválidas")
            
            # Verificar que el usuario esté activo
            if not user.is_active:
                logger.warning(f"Intento de login de usuario inactivo: {request.email}")
                raise ValueError("Usuario desactivado")
            
            # Verificar contraseña
            if not User.verify_password(request.password, user.password_hash):
                logger.warning(f"Contraseña incorrecta para usuario: {request.email}")
                raise ValueError("Credenciales inválidas")
            
            # Actualizar último login
            await self.user_repository.update_last_login(user.id)
            
            # Generar tokens
            access_token = self._create_access_token(user)
            refresh_token = self._create_refresh_token(user)
            
            logger.info(f"Usuario autenticado exitosamente: {user.email}")
            
            return TokenResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                token_type="bearer",
                expires_in=self.access_token_expire_minutes * 60
            )
            
        except ValueError as e:
            logger.error(f"Error de validación en autenticación: {e}")
            raise
        except Exception as e:
            logger.error(f"Error inesperado en autenticación: {e}")
            raise Exception("Error interno del servidor")
    
    def _create_access_token(self, user: User) -> str:
        """Crea un token de acceso JWT"""
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        to_encode = {
            "sub": user.id,
            "email": user.email,
            "username": user.username,
            "role": user.role,
            "exp": expire
        }
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
    
    def _create_refresh_token(self, user: User) -> str:
        """Crea un token de refresh JWT"""
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        to_encode = {
            "sub": user.id,
            "type": "refresh",
            "exp": expire
        }
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
    
    def verify_token(self, token: str) -> Optional[dict]:
        """Verifica y decodifica un token JWT"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token expirado")
            return None
        except jwt.JWTError as e:
            logger.warning(f"Token inválido: {e}")
            return None
    
    async def get_current_user(self, token: str) -> Optional[User]:
        """Obtiene el usuario actual basado en el token"""
        payload = self.verify_token(token)
        if payload is None:
            return None
        
        user_id = payload.get("sub")
        if user_id is None:
            return None
        
        user = await self.user_repository.get_by_id(user_id)
        if user is None or not user.is_active:
            return None
        
        return user
    
    async def refresh_access_token(self, refresh_token: str) -> Optional[TokenResponse]:
        """Refresca un token de acceso usando un refresh token"""
        try:
            payload = jwt.decode(refresh_token, self.secret_key, algorithms=[self.algorithm])
            
            if payload.get("type") != "refresh":
                raise ValueError("Token inválido")
            
            user_id = payload.get("sub")
            if user_id is None:
                raise ValueError("Token inválido")
            
            user = await self.user_repository.get_by_id(user_id)
            if user is None or not user.is_active:
                raise ValueError("Usuario no encontrado o inactivo")
            
            # Generar nuevo access token
            new_access_token = self._create_access_token(user)
            
            return TokenResponse(
                access_token=new_access_token,
                refresh_token=refresh_token,  # Mantener el mismo refresh token
                token_type="bearer",
                expires_in=self.access_token_expire_minutes * 60
            )
            
        except jwt.ExpiredSignatureError:
            logger.warning("Refresh token expirado")
            raise ValueError("Refresh token expirado")
        except jwt.JWTError as e:
            logger.warning(f"Refresh token inválido: {e}")
            raise ValueError("Refresh token inválido")
        except Exception as e:
            logger.error(f"Error refrescando token: {e}")
            raise Exception("Error interno del servidor")
