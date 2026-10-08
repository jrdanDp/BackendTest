from datetime import datetime
from typing import Generic, Optional, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """Estructura estandarizada de respuestas de la API."""
    success: bool = Field(default=True, description="Indica si la operación fue exitosa")
    message: str = Field(default="Operación exitosa", description="Mensaje informativo")
    data: Optional[T] = Field(default=None, description="Carga útil de la respuesta")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Fecha y hora UTC de la respuesta")
