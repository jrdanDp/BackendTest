from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_automation_service, get_db
from app.schemas.automation import (
    CobrosRequest,
    CobrosResponseData,
    NormalizeOnlyRequest,
    OrdenesRequest,
    OrdenesResponseData,
    OrdenesSyncResponseData
)
from app.schemas.common import ApiResponse
from app.services.automation_service import AutomationService

router = APIRouter()


@router.post(
    "/cobros",
    response_model=ApiResponse[CobrosResponseData],
    status_code=status.HTTP_200_OK,
    summary="Ejecutar descarga y normalización de cobros"
)
def ejecutar_cobros(
    payload: CobrosRequest,
    service: AutomationService = Depends(get_automation_service)
):
    """
    Dispara el proceso completo:
    - Autenticación en Scordsoft.
    - Descarga del reporte de cobros según el rango de fechas.
    - Limpieza y normalización de columnas y formatos a Excel.
    """
    resultado = service.ejecutar_flujo_cobros(payload)
    return ApiResponse(
        success=True,
        message="Automatización completada exitosamente.",
        data=resultado
    )


@router.post(
    "/normalizar",
    response_model=ApiResponse[dict],
    status_code=status.HTTP_200_OK,
    summary="Normalizar un archivo Excel existente"
)
def normalizar_archivo(
    payload: NormalizeOnlyRequest,
    service: AutomationService = Depends(get_automation_service)
):
    """
    Aplica las reglas de normalización a un archivo previamente descargado.
    """
    ruta_normalizada = service.normalizar_archivo(payload.archivo_path)
    return ApiResponse(
        success=True,
        message="Archivo normalizado con éxito.",
        data={"archivo_normalizado": ruta_normalizada}
    )


@router.post(
    "/ordenes",
    response_model=ApiResponse[OrdenesResponseData],
    status_code=status.HTTP_200_OK,
    summary="Descargar reporte de Órdenes de Servicio en Excel"
)
def descargar_ordenes(
    payload: OrdenesRequest,
    service: AutomationService = Depends(get_automation_service)
):
    """
    Descarga el reporte de Órdenes de Servicio:
    - Fechas por defecto: primer día del mes actual a la fecha de hoy.
    - Se guarda en Documentos/Ordenes/
    """
    resultado = service.ejecutar_descarga_ordenes(payload)
    return ApiResponse(
        success=True,
        message="Reporte de órdenes descargado exitosamente.",
        data=resultado
    )


@router.post(
    "/ordenes/sincronizar",
    response_model=ApiResponse[OrdenesSyncResponseData],
    status_code=status.HTTP_200_OK,
    summary="Flujo completo: Descargar, normalizar y cargar órdenes en BD"
)
async def sincronizar_ordenes(
    payload: OrdenesRequest,
    service: AutomationService = Depends(get_automation_service),
    db: AsyncSession = Depends(get_db)
):
    """
    Ejecuta el flujo completo de principio a fin:
    1. Descarga el reporte Excel de órdenes de ScordSoft.
    2. Normaliza y genera el archivo limpio en Documentos/Ordenes/Normalizados/.
    3. Carga en la base de datos en las tablas 'ordenes' y 'asignacion_ordenes'.
    4. Vincula técnicos en 'personal' y clientes existentes.
    """
    resultado = await service.ejecutar_flujo_completo_ordenes(payload, db)
    return ApiResponse(
        success=True,
        message="Órdenes descargadas, normalizadas y sincronizadas en la base de datos exitosamente.",
        data=resultado
    )


@router.post(
    "/ordenes/normalizar",
    response_model=ApiResponse[dict],
    status_code=status.HTTP_200_OK,
    summary="Normalizar un archivo Excel de órdenes existente y cargarlo a BD"
)
async def normalizar_ordenes_archivo(
    payload: NormalizeOnlyRequest,
    service: AutomationService = Depends(get_automation_service),
    db: AsyncSession = Depends(get_db)
):
    """
    Toma un archivo Excel ya descargado, lo normaliza e inserta en la base de datos.
    """
    ruta_norm, metricas = await service.normalizar_y_cargar_ordenes(payload.archivo_path, db)
    return ApiResponse(
        success=True,
        message="Archivo normalizado y cargado a la base de datos exitosamente.",
        data={
            "archivo_normalizado": ruta_norm,
            **metricas
        }
    )


