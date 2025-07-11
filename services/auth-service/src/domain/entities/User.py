from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field
import bcrypt
import re

class User(BaseModel):
    """Entidad de usuario del dominio"""
    
    id: Optional[str] = None
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password_hash: str
    is_active: bool = True
    is_verified: bool = False
    role: str = "user"  # user, admin, moderator
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    @staticmethod
    def validate_password(password: str) -> bool:
        """Valida que la contraseña cumpla con los requisitos de seguridad"""
        if len(password) < 8:
            return False
        
        # Debe contener al menos una letra mayúscula, una minúscula y un número
        if not re.search(r'[A-Z]', password):
            return False
        if not re.search(r'[a-z]', password):
            return False
        if not re.search(r'\d', password):
            return False
        
        return True
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Genera el hash de la contraseña usando bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """Verifica si la contraseña coincide con el hash"""
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    
    def to_dict(self) -> dict:
        """Convierte la entidad a diccionario para MongoDB"""
        user_dict = self.dict()
        if self.id:
            user_dict['_id'] = self.id
        return user_dict
    
    @classmethod
    def from_dict(cls, data: dict) -> 'User':
        """Crea una instancia de User desde un diccionario de MongoDB"""
        if '_id' in data:
            data['id'] = str(data['_id'])
            del data['_id']
        return cls(**data)
