import os
import sys
import re
import argparse
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup

# Asegurar que el directorio raíz del proyecto esté en sys.path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from config import URL_ORDENES_FILTER, BASE_REPORTES, DIR_ORDENES, DIR_ORDENES_NORMALIZADOS
from Scrapper.login import login
from Utils.utilsDate import (
    obtener_fecha_hoy_str,
    obtener_primer_dia_mes_str,
    obtener_timestamp_actual,
    validar_rango_fechas
)
from Utils.utilsScrapper import extraer_input_valor, extraer_tokens_aspnet
from Utils.utilsFiles import asegurar_directorio


def descargar_registro_ordenes(
    session: requests.Session = None,
    fecha_inicial: str = None,
    fecha_final: str = None,
    directorio_destino: str = DIR_ORDENES
) -> str:
    """
    Navega al formulario de Ordenes de Servicio (Cronograma de Trabajo OS):
    URL: https://tvch.scordsoft.com/CReportes/Rep_OrdenServicioCronoTrabajoOS_Filter.aspx

    Parámetros configurables:
    - fecha_inicial: Por defecto el primer día del mes actual (DD/MM/YYYY).
    - fecha_final: Por defecto el día actual (DD/MM/YYYY).
    - btnEjecutar: 'Procesar'.

    Descarga el archivo Excel (.xlsx) y lo guarda en Documentos/Ordenes/
    con el formato: Cronograma_Ordenes_[timestamp].xlsx
    """
    if session is None:
        print("[*] Sesión no provista. Iniciando autenticación automática...")
        exito, session = login()
        if not exito:
            raise RuntimeError("Fallo en la autenticación para descargar órdenes.")

    # 1. Resolver fechas por defecto:
    # fecha_inicial: primer día del mes actual (ej: 01/10/2026)
    # fecha_final: fecha actual (ej: 07/10/2026)
    fecha_inicial = fecha_inicial or obtener_primer_dia_mes_str()
    fecha_final = fecha_final or obtener_fecha_hoy_str()

    # Validación de formato y rango de fechas
    validar_rango_fechas(fecha_inicial, fecha_final)
    print(f"[*] Rango de fechas configurado: {fecha_inicial} hasta {fecha_final}")

    # 2. Petición GET para obtener estado ASP.NET del formulario
    print(f"[*] Solicitando formulario de órdenes: {URL_ORDENES_FILTER}")
    res_get = session.get(URL_ORDENES_FILTER)
    res_get.raise_for_status()

    soup = BeautifulSoup(res_get.text, "html.parser")
    tokens = extraer_tokens_aspnet(soup)

    # Identificar filial seleccionada en el formulario
    ddl_filial = soup.find("select", {"name": "ctl00$MainContent$ddlFilial"})
    filial_val = "2"
    if ddl_filial:
        selected_option = ddl_filial.find("option", selected=True)
        if selected_option:
            filial_val = selected_option.get("value", "2")

    # 3. Construir payload con los campos especificados
    payload = {
        **tokens,
        "ctl00_MainContent_tsmForm_HiddenField": "",
        "ctl00$tvwMenu_ExpandState": extraer_input_valor(soup, "ctl00_tvwMenu_ExpandState"),
        "ctl00$tvwMenu_SelectedNode": extraer_input_valor(soup, "ctl00_tvwMenu_SelectedNode"),
        "ctl00$tvwMenu_PopulateLog": extraer_input_valor(soup, "ctl00_tvwMenu_PopulateLog"),
        "ctl00$MainContent$ddlFilial": filial_val,
        "ctl00$MainContent$txtfechainicial": fecha_inicial,
        "ctl00$MainContent$mee2_ClientState": "",
        "ctl00$MainContent$txtfechafinal": fecha_final,
        "ctl00$MainContent$mee1_ClientState": "",
        "ctl00$MainContent$rdbseleccion": "0",
        "ctl00$MainContent$TipoSalidaReporte": "rbnXls",
        "ctl00$MainContent$btnEjecutar": "Procesar"
    }

    headers_post = {
        "Origin": "https://tvch.scordsoft.com",
        "Referer": URL_ORDENES_FILTER,
        "Content-Type": "application/x-www-form-urlencoded"
    }

    print("[*] Enviando solicitud para procesar reporte de órdenes...")
    res_post = session.post(URL_ORDENES_FILTER, data=payload, headers=headers_post)
    res_post.raise_for_status()

    # 4. Detectar la llamada window.open en el script emitido por ASP.NET
    popup_match = re.search(r"window\.open\('([^']+)'", res_post.text)
    if not popup_match:
        soup_post = BeautifulSoup(res_post.text, "html.parser")
        lbl_msg = soup_post.find(id="ctl00_MainContent_lblMsg")
        msg = lbl_msg.get_text(strip=True) if lbl_msg else "No se detectó el enlace de descarga del reporte de órdenes."
        raise RuntimeError(f"Error al generar reporte de órdenes: {msg}")

    url_descarga_rel = popup_match.group(1)
    url_descarga_abs = urljoin(BASE_REPORTES, url_descarga_rel)
    print(f"[*] Endpoint de descarga detectado: {url_descarga_abs}")

    # 5. Descargar el archivo Excel (.xlsx)
    res_archivo = session.get(url_descarga_abs, headers={"Referer": URL_ORDENES_FILTER})
    res_archivo.raise_for_status()

    # 6. Asegurar directorios destino y la subcarpeta de normalización para la siguiente fase
    asegurar_directorio(directorio_destino)
    asegurar_directorio(DIR_ORDENES_NORMALIZADOS)

    timestamp = obtener_timestamp_actual()
    nombre_archivo = f"Cronograma_Ordenes_{timestamp}.xlsx"
    ruta_guardado = os.path.join(directorio_destino, nombre_archivo)

    with open(ruta_guardado, "wb") as f:
        f.write(res_archivo.content)

    print(f"[+] Archivo de órdenes guardado correctamente en: {ruta_guardado}")
    return ruta_guardado


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Automatización de descarga de Órdenes de Servicio (Excel)")
    parser.add_argument("--ini", help="Fecha inicial DD/MM/YYYY (por defecto primero del mes)", default=None)
    parser.add_argument("--fin", help="Fecha final DD/MM/YYYY (por defecto hoy)", default=None)
    args = parser.parse_args()

    descargar_registro_ordenes(fecha_inicial=args.ini, fecha_final=args.fin)
