import os
import requests
from typing import Optional, Tuple

from app.core.exceptions import AuthenticationError, AutomationError, NormalizationError, ResourceNotFoundError
from Scrapper.login import login
from Scrapper.registroCobros import descargar_registro_cobros
from dataNormalizer import normalizar_registro_cobros


class ScrapperClient:
    """
    Cliente/Adaptador de infraestructura que encapsula la interacción
    con el scrapper de Scordsoft y el motor de normalización.
    """

    def autenticar(self) -> requests.Session:
        """Inicia sesión en el portal Scordsoft y retorna la sesión HTTP."""
        try:
            login_ok, session = login()
            if not login_ok or session is None:
                raise AuthenticationError("Credenciales inválidas o fallo al autenticar en Scordsoft.")
            return session
        except AuthenticationError:
            raise
        except Exception as exc:
            raise AutomationError(f"Error de conexión durante el login: {str(exc)}") from exc

    def descargar_cobros(
        self,
        session: requests.Session,
        fecha_inicial: Optional[str] = None,
        fecha_final: Optional[str] = None
    ) -> str:
        """Descarga el reporte de cobros para el rango de fechas indicado."""
        try:
            ruta_archivo = descargar_registro_cobros(
                session=session,
                fecha_inicial=fecha_inicial,
                fecha_final=fecha_final
            )
            if not os.path.exists(ruta_archivo):
                raise AutomationError(f"El reporte de cobros no fue encontrado en la ruta esperada: {ruta_archivo}")
            return ruta_archivo
        except Exception as exc:
            raise AutomationError(f"Fallo durante la descarga del reporte: {str(exc)}") from exc

    def descargar_ordenes(
        self,
        session: requests.Session,
        fecha_inicial: Optional[str] = None,
        fecha_final: Optional[str] = None
    ) -> str:
        """Descarga el reporte de órdenes de servicio en Excel."""
        from Scrapper.ordenes import descargar_registro_ordenes
        try:
            ruta_archivo = descargar_registro_ordenes(
                session=session,
                fecha_inicial=fecha_inicial,
                fecha_final=fecha_final
            )
            if not os.path.exists(ruta_archivo):
                raise AutomationError(f"El reporte de órdenes no fue encontrado en la ruta esperada: {ruta_archivo}")
            return ruta_archivo
        except Exception as exc:
            raise AutomationError(f"Fallo durante la descarga del reporte de órdenes: {str(exc)}") from exc

    def normalizar_archivo(self, ruta_archivo: str) -> str:
        """Ejecuta la normalización de datos sobre un archivo Excel generado."""
        if not os.path.exists(ruta_archivo):
            raise ResourceNotFoundError(f"No existe el archivo especificado para normalizar: {ruta_archivo}")

        try:
            ruta_normalizada = normalizar_registro_cobros(ruta_archivo)
            if not os.path.exists(ruta_normalizada):
                raise NormalizationError("El proceso de normalización no generó el archivo de salida.")
            return ruta_normalizada
        except ResourceNotFoundError:
            raise
        except Exception as exc:
            raise NormalizationError(f"Fallo durante la normalización del archivo: {str(exc)}") from exc
