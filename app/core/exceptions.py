from fastapi import Request
from fastapi.responses import JSONResponse


class AppException(Exception):
    """Excepción base para errores de negocio de la aplicación."""
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class AuthenticationError(AppException):
    """Error al autenticar con el portal externo / scrapper."""
    def __init__(self, message: str = "Fallo en la autenticación con el sistema externo."):
        super().__init__(message=message, status_code=401)


class AutomationError(AppException):
    """Error general durante el proceso de automatización."""
    def __init__(self, message: str = "Error durante el flujo de automatización.", status_code: int = 500):
        super().__init__(message=message, status_code=status_code)


class NormalizationError(AppException):
    """Error durante la normalización de datos."""
    def __init__(self, message: str = "Error al procesar y normalizar el archivo."):
        super().__init__(message=message, status_code=422)


class ResourceNotFoundError(AppException):
    """Recurso o archivo no encontrado."""
    def __init__(self, message: str = "Recurso no encontrado."):
        super().__init__(message=message, status_code=404)


async def app_exception_handler(request: Request, exc: AppException):
    """Manejador global para AppException."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "type": exc.__class__.__name__,
                "message": exc.message,
                "status_code": exc.status_code,
            }
        }
    )
