"""
Capa de Repositorios (Acceso a Datos): Abstracción sobre la base de datos.
"""
from app.repositories.base import BaseRepository
from app.repositories.orden_repository import OrdenRepository

__all__ = ["BaseRepository", "OrdenRepository"]

