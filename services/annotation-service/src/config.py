from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_TITLE: str = "BrainLens Annotation Service"
    APP_DESCRIPTION: str = "Servicio para gestión de anotaciones médicas"
    APP_VERSION: str = "1.0.0"
    ALLOW_ORIGINS: list[str] = ["*"]  # Cambiar en producción
    HOST: str = "0.0.0.0"
    PORT: int = 8003
    DEBUG: bool = False

    class Config:
        env_file = ".env"

settings = Settings()
