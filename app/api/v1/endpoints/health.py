from fastapi import APIRouter
from app.core.config import settings
from app.core.database import ping_database
from app.schemas.automation import HealthResponse
from app.schemas.common import ApiResponse

router = APIRouter()


@router.get("", response_model=ApiResponse[HealthResponse], summary="Estado de la aplicación y Base de Datos")
async def health_check():
    """Retorna el estado de disponibilidad del backend y la conexión a PostgreSQL."""
    db_connected = await ping_database()
    data = HealthResponse(
        status="ok" if db_connected else "degraded",
        app_name=settings.PROJECT_NAME,
        version=settings.VERSION,
        environment="development" if settings.DEBUG else "testing",
        database="connected" if db_connected else "disconnected"
    )
    return ApiResponse(
        success=db_connected,
        message="Backend y Base de Datos operativos." if db_connected else "Backend activo pero BD desconectada.",
        data=data
    )

