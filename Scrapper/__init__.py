"""Paquete de scrapers para la plataforma ScordSoft."""
from .login import login
from .registroCobros import descargar_registro_cobros
from .ordenes import descargar_registro_ordenes

__all__ = ["login", "descargar_registro_cobros", "descargar_registro_ordenes"]

