from typing import Any, Generic, List, Optional, Type, TypeVar
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """
    Repositorio base genérico para operaciones CRUD asíncronas en la base de datos.
    Permite desacoplar los servicios de las queries directas de SQLAlchemy.
    """

    def __init__(self, model: Type[ModelType], session: AsyncSession):
        self.model = model
        self.session = session

    async def get_by_id(self, id_val: Any) -> Optional[ModelType]:
        """Obtiene un registro por su ID primario."""
        return await self.session.get(self.model, id_val)

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """Lista registros con paginación básica."""
        query = select(self.model).offset(skip).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def create(self, instance: ModelType) -> ModelType:
        """Persiste una nueva entidad en la base de datos."""
        self.session.add(instance)
        await self.session.commit()
        await self.session.refresh(instance)
        return instance

    async def update(self, instance: ModelType) -> ModelType:
        """Actualiza una entidad existente."""
        await self.session.commit()
        await self.session.refresh(instance)
        return instance

    async def delete(self, instance: ModelType) -> None:
        """Elimina una entidad."""
        await self.session.delete(instance)
        await self.session.commit()
