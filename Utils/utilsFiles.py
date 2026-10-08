import os

def asegurar_directorio(ruta_directorio: str) -> str:
    """Crea la carpeta si no existe y retorna la ruta normalizada."""
    os.makedirs(ruta_directorio, exist_ok=True)
    return ruta_directorio
