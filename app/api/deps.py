from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.infrastructure.scrapper_client import ScrapperClient
from app.services.automation_service import AutomationService


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Inyector de dependencia para la sesión de base de datos PostgreSQL."""
    async for session in get_db_session():
        yield session


def get_scrapper_client() -> ScrapperClient:
    """Provee una instancia del cliente de infraestructura."""
    return ScrapperClient()


def get_automation_service() -> AutomationService:
    """Provee una instancia del servicio de automatización con inyección de dependencias."""
    client = get_scrapper_client()
    return AutomationService(scrapper_client=client)

