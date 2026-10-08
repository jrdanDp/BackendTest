from typing import Optional
from pydantic import BaseModel, Field, field_validator
import re

DATE_REGEX = r"^\d{2}/\d{2}/\d{4}$"


class CobrosRequest(BaseModel):
    """Parámetros de entrada para ejecutar la descarga y procesamiento de cobros."""
    fecha_inicial: Optional[str] = Field(
        default=None,
        description="Fecha inicial en formato DD/MM/YYYY (opcional, por defecto día actual)",
        examples=["01/10/2026"]
    )
    fecha_final: Optional[str] = Field(
        default=None,
        description="Fecha final en formato DD/MM/YYYY (opcional, por defecto día actual)",
        examples=["07/10/2026"]
    )

    @field_validator("fecha_inicial", "fecha_final")
    @classmethod
    def validar_formato_fecha(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not re.match(DATE_REGEX, v):
            raise ValueError("El formato de fecha debe ser estrictamente DD/MM/YYYY (ej: '01/10/2026').")
        return v


class CobrosResponseData(BaseModel):
    """Datos retornados tras la descarga y normalización de cobros."""
    archivo_original: str = Field(description="Ruta del archivo Excel descargado originalmente")
    archivo_normalizado: str = Field(description="Ruta del archivo Excel normalizado")
    fecha_inicial: str = Field(description="Fecha inicial aplicada")
    fecha_final: str = Field(description="Fecha final aplicada")


class NormalizeOnlyRequest(BaseModel):
    """Parámetros para solicitar solo la normalización de un archivo existente."""
    archivo_path: str = Field(description="Ruta relativa o absoluta del archivo Excel a normalizar")


class OrdenesRequest(BaseModel):
    """Parámetros para solicitar la descarga de órdenes de servicio."""
    fecha_inicial: Optional[str] = Field(
        default=None,
        description="Fecha inicial DD/MM/YYYY (opcional, por defecto primer día del mes actual)",
        examples=["01/10/2026"]
    )
    fecha_final: Optional[str] = Field(
        default=None,
        description="Fecha final DD/MM/YYYY (opcional, por defecto fecha de hoy)",
        examples=["07/10/2026"]
    )

    @field_validator("fecha_inicial", "fecha_final")
    @classmethod
    def validar_formato_fecha(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not re.match(DATE_REGEX, v):
            raise ValueError("El formato de fecha debe ser estrictamente DD/MM/YYYY (ej: '01/10/2026').")
        return v


class OrdenesResponseData(BaseModel):
    """Datos retornados tras la descarga del reporte de órdenes."""
    archivo_descargado: str = Field(description="Ruta del archivo Excel de órdenes descargado")
    fecha_inicial: str = Field(description="Fecha inicial aplicada")
    fecha_final: str = Field(description="Fecha final aplicada")


class OrdenesSyncResponseData(BaseModel):
    """Datos retornados tras descargar, normalizar y sincronizar con la base de datos."""
    archivo_original: str = Field(description="Ruta del archivo Excel descargado de Scordsoft")
    archivo_normalizado: str = Field(description="Ruta del archivo Excel normalizado generado")
    fecha_inicial: str = Field(description="Fecha inicial de consulta aplicada")
    fecha_final: str = Field(description="Fecha final de consulta aplicada")
    ordenes_procesadas: int = Field(description="Cantidad total de órdenes procesadas")
    ordenes_sincronizadas: int = Field(description="Cantidad de órdenes insertadas o actualizadas en BD")
    asignaciones_creadas: int = Field(description="Cantidad de asignaciones registradas en 'asignacion_ordenes'")
    tecnicos_nuevos: int = Field(description="Cantidad de técnicos creados automáticamente en 'personal'")




class HealthResponse(BaseModel):
    """Respuesta del estado del servicio."""
    status: str = "ok"
    app_name: str
    version: str
    environment: str = "testing"
    database: str = Field(default="unknown", description="Estado de conexión con PostgreSQL")

