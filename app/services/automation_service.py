from typing import Optional, Dict, Tuple
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.scrapper_client import ScrapperClient
from app.schemas.automation import CobrosRequest, CobrosResponseData
from Utils.utilsDate import obtener_fecha_hoy_str, validar_rango_fechas
from app.core.exceptions import AppException


class AutomationService:
    """
    Servicio de Dominio / Caso de Uso:
    Contiene la lógica de negocio para la orquestación del proceso de automatización.
    """

    def __init__(self, scrapper_client: Optional[ScrapperClient] = None):
        self.scrapper_client = scrapper_client or ScrapperClient()

    def ejecutar_flujo_cobros(self, request: CobrosRequest) -> CobrosResponseData:
        """
        Orquesta el flujo completo de cobros:
        1. Resuelve y valida fechas de inicio y fin.
        2. Autentica contra el sistema de origen.
        3. Descarga el reporte sin procesar.
        4. Normaliza la información.
        5. Devuelve la metadata y rutas resultantes.
        """
        hoy = obtener_fecha_hoy_str()
        fecha_ini = request.fecha_inicial or hoy
        fecha_fin = request.fecha_final or hoy

        # Validación de reglas de fechas de negocio
        try:
            validar_rango_fechas(fecha_ini, fecha_fin)
        except ValueError as exc:
            raise AppException(message=str(exc), status_code=400) from exc

        # 1. Login
        session = self.scrapper_client.autenticar()

        # 2. Descargar reporte
        ruta_original = self.scrapper_client.descargar_cobros(
            session=session,
            fecha_inicial=fecha_ini,
            fecha_final=fecha_fin
        )

        # 3. Normalizar reporte
        ruta_normalizada = self.scrapper_client.normalizar_archivo(ruta_original)

        return CobrosResponseData(
            archivo_original=ruta_original,
            archivo_normalizado=ruta_normalizada,
            fecha_inicial=fecha_ini,
            fecha_final=fecha_fin
        )

    def normalizar_archivo(self, ruta_archivo: str) -> str:
        """
        Caso de uso para normalizar un archivo ya descargado.
        """
        return self.scrapper_client.normalizar_archivo(ruta_archivo)

    def ejecutar_descarga_ordenes(self, request: "OrdenesRequest") -> "OrdenesResponseData":
        """
        Caso de uso para la descarga del Excel de Órdenes de Servicio:
        1. Resuelve fechas por defecto (primer día de mes actual y día de hoy).
        2. Valida rango de fechas.
        3. Autentica y descarga reporte a Documentos/Ordenes/.
        """
        from app.schemas.automation import OrdenesResponseData
        from Utils.utilsDate import obtener_primer_dia_mes_str

        fecha_ini = request.fecha_inicial or obtener_primer_dia_mes_str()
        fecha_fin = request.fecha_final or obtener_fecha_hoy_str()

        try:
            validar_rango_fechas(fecha_ini, fecha_fin)
        except ValueError as exc:
            raise AppException(message=str(exc), status_code=400) from exc

        session = self.scrapper_client.autenticar()
        ruta_descarga = self.scrapper_client.descargar_ordenes(
            session=session,
            fecha_inicial=fecha_ini,
            fecha_final=fecha_fin
        )

        return OrdenesResponseData(
            archivo_descargado=ruta_descarga,
            fecha_inicial=fecha_ini,
            fecha_final=fecha_fin
        )

    async def normalizar_y_cargar_ordenes(
        self,
        ruta_archivo: str,
        db: "AsyncSession"
    ) -> Tuple[str, Dict[str, int]]:
        """
        Caso de uso: Lee un Excel bruto de órdenes, lo normaliza guardando el Excel limpio,
        e inserta o actualiza en la base de datos (ordenes y asignacion_ordenes).
        """
        from ordenesNormalizer import normalizar_registro_ordenes
        from app.repositories.orden_repository import OrdenRepository

        ruta_norm, df_norm = normalizar_registro_ordenes(ruta_archivo)
        repo = OrdenRepository(session=db)
        metricas = await repo.sync_ordenes_and_asignaciones(df_norm)
        return ruta_norm, metricas

    async def ejecutar_flujo_completo_ordenes(
        self,
        request: "OrdenesRequest",
        db: "AsyncSession"
    ) -> "OrdenesSyncResponseData":
        """
        Caso de uso integral:
        1. Descarga el Excel de órdenes de Scordsoft.
        2. Normaliza el archivo a Excel en Documentos/Ordenes/Normalizados/.
        3. Carga e inserta las órdenes y asignaciones en PostgreSQL.
        """
        from app.schemas.automation import OrdenesSyncResponseData
        from Utils.utilsDate import obtener_primer_dia_mes_str

        fecha_ini = request.fecha_inicial or obtener_primer_dia_mes_str()
        fecha_fin = request.fecha_final or obtener_fecha_hoy_str()

        # 1. Descargar
        session = self.scrapper_client.autenticar()
        ruta_descarga = self.scrapper_client.descargar_ordenes(
            session=session,
            fecha_inicial=fecha_ini,
            fecha_final=fecha_fin
        )

        # 2 y 3. Normalizar y sincronizar con BD
        ruta_norm, metricas = await self.normalizar_y_cargar_ordenes(ruta_descarga, db)

        return OrdenesSyncResponseData(
            archivo_original=ruta_descarga,
            archivo_normalizado=ruta_norm,
            fecha_inicial=fecha_ini,
            fecha_final=fecha_fin,
            ordenes_procesadas=metricas["ordenes_procesadas"],
            ordenes_sincronizadas=metricas["ordenes_sincronizadas"],
            asignaciones_creadas=metricas["asignaciones_creadas"],
            tecnicos_nuevos=metricas["tecnicos_nuevos"]
        )


