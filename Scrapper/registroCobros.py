import os
import re
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup

from config import URL_COBROS_FILTER, BASE_REPORTES, DIR_REGISTRO_COBROS
from Scrapper.login import login
from Utils.utilsDate import obtener_fecha_hoy_str, obtener_timestamp_actual, validar_rango_fechas
from Utils.utilsScrapper import extraer_input_valor, extraer_tokens_aspnet
from Utils.utilsFiles import asegurar_directorio

def descargar_registro_cobros(
    session: requests.Session = None,
    fecha_inicial: str = None,
    fecha_final: str = None,
    directorio_destino: str = DIR_REGISTRO_COBROS
) -> str:
    """
    Navega a la pantalla de Cobros/Reporte de Ventas con la sesión autenticada,
    configura las fechas y dispara la descarga del archivo Excel (.xlsx).

    Guarda el archivo en directorio_destino con el formato: RegistroVentas_[timestamp].xlsx
    Retorna la ruta absoluta o relativa del archivo descargado.
    """
    if session is None:
        print("[*] Sesión no provista. Iniciando autenticación automática...")
        exito, session = login()
        if not exito:
            raise RuntimeError("Fallo en la autenticación para descargar cobros.")

    # Fechas por defecto (fecha de hoy)
    hoy = obtener_fecha_hoy_str()
    fecha_inicial = fecha_inicial or hoy
    fecha_final = fecha_final or hoy

    # Validación de fechas
    validar_rango_fechas(fecha_inicial, fecha_final)
    print(f"[*] Rango de fechas configurado: {fecha_inicial} hasta {fecha_final}")

    # 1. Petición GET para obtener estado ASP.NET del formulario
    print(f"[*] Solicitando formulario de cobros: {URL_COBROS_FILTER}")
    res_get = session.get(URL_COBROS_FILTER)
    res_get.raise_for_status()

    soup = BeautifulSoup(res_get.text, "html.parser")
    tokens = extraer_tokens_aspnet(soup)

    # Identificar valor de la filial seleccionada
    ddl_filial = soup.find("select", {"name": "ctl00$MainContent$ddlFilial"})
    filial_val = "2"
    if ddl_filial:
        selected_option = ddl_filial.find("option", selected=True)
        if selected_option:
            filial_val = selected_option.get("value", "2")

    # 2. Construir payload para el POST
    payload = {
        **tokens,
        "ctl00_MainContent_tsmForm_HiddenField": "",
        "ctl00$tvwMenu_ExpandState": extraer_input_valor(soup, "ctl00_tvwMenu_ExpandState"),
        "ctl00$tvwMenu_SelectedNode": extraer_input_valor(soup, "ctl00_tvwMenu_SelectedNode"),
        "ctl00$tvwMenu_PopulateLog": extraer_input_valor(soup, "ctl00_tvwMenu_PopulateLog"),
        "ctl00$MainContent$ddlFilial": filial_val,
        "ctl00$MainContent$ddlTipoComprobante": "0",
        "ctl00$MainContent$ddlContribuyente": "0",
        "ctl00$MainContent$ddlNumSerie": "0",
        "ctl00$MainContent$txtFechaInicial": fecha_inicial,
        "ctl00$MainContent$MaskedEditExtender2_ClientState": "",
        "ctl00$MainContent$txtFechaFinal": fecha_final,
        "ctl00$MainContent$MaskedEditExtender3_ClientState": "",
        "ctl00$MainContent$TipoSalidaReporte": "rbnXls",
        "ctl00$MainContent$TipoFiltroFecha": "rbnFechaEmision",
        "ctl00$MainContent$btnEjecutar": "Registro Ventas"
    }

    headers_post = {
        "Origin": "https://tvch.scordsoft.com",
        "Referer": URL_COBROS_FILTER,
        "Content-Type": "application/x-www-form-urlencoded"
    }

    print("[*] Enviando solicitud para generar reporte...")
    res_post = session.post(URL_COBROS_FILTER, data=payload, headers=headers_post)
    res_post.raise_for_status()

    # 3. Detectar la llamada window.open en el script emitido por ASP.NET
    popup_match = re.search(r"window\.open\('([^']+)'", res_post.text)
    if not popup_match:
        soup_post = BeautifulSoup(res_post.text, "html.parser")
        lbl_msg = soup_post.find(id="ctl00_MainContent_lblMsg")
        msg = lbl_msg.get_text(strip=True) if lbl_msg else "No se detectó el enlace de descarga del reporte."
        raise RuntimeError(f"Error al generar reporte: {msg}")

    url_descarga_rel = popup_match.group(1)
    url_descarga_abs = urljoin(BASE_REPORTES, url_descarga_rel)
    print(f"[*] Endpoint de descarga detectado: {url_descarga_abs}")

    # 4. Descargar el archivo Excel (.xlsx)
    res_archivo = session.get(url_descarga_abs, headers={"Referer": URL_COBROS_FILTER})
    res_archivo.raise_for_status()

    # 5. Guardar en Documentos/RegistroCobros con formato de fecha de descarga
    asegurar_directorio(directorio_destino)
    timestamp = obtener_timestamp_actual()
    nombre_archivo = f"RegistroVentas_{timestamp}.xlsx"
    ruta_guardado = os.path.join(directorio_destino, nombre_archivo)

    with open(ruta_guardado, "wb") as f:
        f.write(res_archivo.content)

    print(f"[+] Archivo guardado correctamente en: {ruta_guardado}")
    return ruta_guardado

if __name__ == "__main__":
    descargar_registro_cobros()
