import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

BASE_URL = os.getenv("SCORD_BASE_URL", "https://tvch.scordsoft.com/")
DEFAULT_USERNAME = os.getenv("SCORD_USER", "")
DEFAULT_PASSWORD = os.getenv("SCORD_PASSWORD", "")

URL_LOGIN = BASE_URL
URL_COBROS_FILTER = f"{BASE_URL}CReportes/Rep_CPagoRegistroVentasMedioPago_Filter.aspx"
URL_ORDENES_FILTER = f"{BASE_URL}CReportes/Rep_OrdenServicioCronoTrabajoOS_Filter.aspx"
BASE_REPORTES = f"{BASE_URL}CReportes/"

# Rutas de almacenamiento
DIR_DOCUMENTOS = "Documentos"
DIR_REGISTRO_COBROS = os.path.join(DIR_DOCUMENTOS, "RegistroCobros")
DIR_REGISTRO_NORMALIZADOS = os.path.join(DIR_DOCUMENTOS, "RegistroCobrosNormalizados")
DIR_ORDENES = os.path.join(DIR_DOCUMENTOS, "Ordenes")
DIR_ORDENES_NORMALIZADOS = os.path.join(DIR_ORDENES, "Normalizados")

# Headers estándar de navegación
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
}
