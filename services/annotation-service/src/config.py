from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_TITLE: str = "BrainLens Annotation Service"
    APP_DESCRIPTION: str = "Servicio para gestión de anotaciones médicas"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    ALB_DNS_NAME: str = ""
    HOST: str = "0.0.0.0"
    PORT: int = 8003
    DEBUG: bool = False

    @property
    def ALLOW_ORIGINS(self) -> list[str]:
        """Configuración dinámica de CORS según el entorno"""
        if self.ENVIRONMENT == "production" and self.ALB_DNS_NAME:
            return [f"http://{self.ALB_DNS_NAME}", f"https://{self.ALB_DNS_NAME}"]
        else:
            return ["http://localhost:3000", "http://127.0.0.1:3000"]

    class Config:
        env_file = ".env"

settings = Settings()
