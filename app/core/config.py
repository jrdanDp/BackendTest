import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Backend de Automatización Scordsoft"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = False

    # Configuración de Scordsoft / Scrapper
    SCORD_BASE_URL: str = os.getenv("SCORD_BASE_URL", "https://tvch.scordsoft.com/")
    SCORD_USER: str = os.getenv("SCORD_USER", "")
    SCORD_PASSWORD: str = os.getenv("SCORD_PASSWORD", "")

    # Rutas de almacenamiento
    DIR_DOCUMENTOS: str = "Documentos"
    DIR_REGISTRO_COBROS: str = os.path.join("Documentos", "RegistroCobros")
    DIR_REGISTRO_NORMALIZADOS: str = os.path.join("Documentos", "RegistroCobrosNormalizados")
    DIR_ORDENES: str = os.path.join("Documentos", "Ordenes")
    DIR_ORDENES_NORMALIZADOS: str = os.path.join("Documentos", "Ordenes", "Normalizados")

    # Base de Datos PostgreSQL (AsyncPG)
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:password@localhost:5432/dbname")
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_ECHO: bool = False

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["*"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
