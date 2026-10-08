import argparse
from Scrapper.login import login
from Scrapper.registroCobros import descargar_registro_cobros
from dataNormalizer import normalizar_registro_cobros
from Utils.utilsDate import obtener_fecha_hoy_str

def ejecutar_automatizacion(fecha_inicial: str = None, fecha_final: str = None):
    """
    Orquestador principal de la automatización:
    1. ScrapperLogin: Autentica y obtiene el objeto session.
    2. ScrapperCobros: Descarga el reporte en Documentos/RegistroCobros.
    3. DataNormalizer: Procesa y genera el archivo limpio en Documentos/RegistroCobrosNormalizados.
    """
    print("=" * 60)
    print("           INICIO DE AUTOMATIZACIÓN - SCORDSOFT            ")
    print("=" * 60)

    # 1. Login
    print("\n--- PASO 1: AUTENTICACIÓN ---")
    login_ok, session = login()
    if not login_ok:
        print("[-] Falló el inicio de sesión. Cancelando proceso.")
        return False

    # 2. Descargar Registro de Cobros (Ventas)
    print("\n--- PASO 2: DESCARGA DE REPORTE DE COBROS ---")
    try:
        ruta_archivo_descargado = descargar_registro_cobros(
            session=session,
            fecha_inicial=fecha_inicial,
            fecha_final=fecha_final
        )
    except Exception as e:
        print(f"[-] Error durante la descarga del reporte: {e}")
        return False

    # 3. Normalizar datos
    print("\n--- PASO 3: NORMALIZACIÓN DE DATOS ---")
    try:
        ruta_normalizada = normalizar_registro_cobros(ruta_archivo_descargado)
    except Exception as e:
        print(f"[-] Error durante la normalización: {e}")
        return False

    print("\n" + "=" * 60)
    print("[+] Automatización completada exitosamente.")
    print(f"    - Archivo Original   : {ruta_archivo_descargado}")
    print(f"    - Archivo Normalizado: {ruta_normalizada}")
    print("=" * 60)
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Automatización de descarga y normalización de Registro de Ventas")
    parser.add_argument("--ini", help="Fecha inicial DD/MM/YYYY (por defecto hoy)", default=None)
    parser.add_argument("--fin", help="Fecha final DD/MM/YYYY (por defecto hoy)", default=None)
    args = parser.parse_args()

    ejecutar_automatizacion(fecha_inicial=args.ini, fecha_final=args.fin)