import os
import re
from datetime import datetime, date, time
from typing import Optional, Tuple
import pandas as pd

from config import DIR_ORDENES_NORMALIZADOS
from Utils.utilsFiles import asegurar_directorio
from Utils.utilsDate import obtener_timestamp_actual


COLUMNAS_ORDEN_INTERES = [
    "id_orden",
    "id_cliente",
    "estado_orden",
    "f_recepcion",
    "hora_recep",
    "f_atencion",
    "hora_inicio",
    "hora_fin",
    "obs_recepcion",
    "obs_descargo",
    "usuario_ing",
    "fecha_ing",
    "tecnico"
]


def parse_time(val) -> Optional[time]:
    """Extrae y formatea una hora a objeto time de Python."""
    if pd.isna(val) or not str(val).strip():
        return None
    s = str(val).strip()
    match = re.search(r"(\d{1,2}):(\d{2})", s)
    if match:
        h, m = int(match.group(1)), int(match.group(2))
        return time(hour=h, minute=m)
    return None


def parse_date(val) -> Optional[date]:
    """Convierte valor a objeto date."""
    if pd.isna(val) or not str(val).strip():
        return None
    try:
        ts = pd.to_datetime(val)
        return ts.date()
    except Exception:
        return None


def parse_datetime(val) -> Optional[datetime]:
    """Convierte valor a objeto datetime."""
    if pd.isna(val) or not str(val).strip():
        return None
    try:
        return pd.to_datetime(val).to_pydatetime()
    except Exception:
        return None


def normalizar_registro_ordenes(
    ruta_archivo_excel: str,
    directorio_destino: str = DIR_ORDENES_NORMALIZADOS
) -> Tuple[str, pd.DataFrame]:
    """
    Lee el archivo Excel bruto descargado de Órdenes de Servicio (Scordsoft),
    detecta la cabecera, extrae y limpia únicamente las columnas requeridas
    para las tablas 'ordenes' y 'asignacion_ordenes', y guarda el Excel normalizado.
    """
    if not os.path.exists(ruta_archivo_excel):
        raise FileNotFoundError(f"El archivo a normalizar no existe: {ruta_archivo_excel}")

    asegurar_directorio(directorio_destino)

    # 1. Detectar en qué fila se encuentra la cabecera real
    df_raw = pd.read_excel(ruta_archivo_excel, header=None)
    header_idx = 0
    for idx, row in df_raw.iterrows():
        row_str = [str(x).strip().upper() for x in row.values]
        if "NUMERO OS" in row_str:
            header_idx = idx
            break

    # 2. Cargar con la fila de cabecera correcta
    df = pd.read_excel(ruta_archivo_excel, header=header_idx)

    # Detectar dinámicamente columna de abonado (Nº ABONADO)
    col_abonado = None
    for col in df.columns:
        c_upper = str(col).upper()
        if "ABONADO" in c_upper and "ESTADO" not in c_upper:
            col_abonado = col
            break

    registros = []
    for _, row in df.iterrows():
        # Descartar filas vacías o sin número de orden
        if pd.isna(row.get("NUMERO OS")):
            continue
        try:
            id_orden = int(row["NUMERO OS"])
        except (ValueError, TypeError):
            continue

        id_cliente = None
        if col_abonado and pd.notna(row.get(col_abonado)):
            try:
                id_cliente = int(row[col_abonado])
            except (ValueError, TypeError):
                id_cliente = None

        estado_orden = str(row.get("EST OS", "REGISTRADA")).strip().upper()
        f_recepcion = parse_date(row.get("F. RECEP"))
        hora_recep = parse_time(row.get("HORA"))
        f_atencion = parse_date(row.get("F ATENC."))
        hora_inicio = parse_time(row.get("HORA I"))
        hora_fin = parse_time(row.get("HORA F"))

        obs_recepcion = str(row.get("OBSERVACION RECEPCION")).strip() if pd.notna(row.get("OBSERVACION RECEPCION")) else None
        obs_descargo = str(row.get("OBSERVACION DESCARGO")).strip() if pd.notna(row.get("OBSERVACION DESCARGO")) else None
        usuario_ing = str(row.get("USUARIO ING.")).strip() if pd.notna(row.get("USUARIO ING.")) else None
        fecha_ing = parse_datetime(row.get("FECHA ING."))
        tecnico = str(row.get("NOMBRES TECNICO")).strip() if pd.notna(row.get("NOMBRES TECNICO")) else None

        registros.append({
            "id_orden": id_orden,
            "id_cliente": id_cliente,
            "estado_orden": estado_orden,
            "f_recepcion": f_recepcion,
            "hora_recep": hora_recep,
            "f_atencion": f_atencion,
            "hora_inicio": hora_inicio,
            "hora_fin": hora_fin,
            "obs_recepcion": obs_recepcion,
            "obs_descargo": obs_descargo,
            "usuario_ing": usuario_ing,
            "fecha_ing": fecha_ing,
            "tecnico": tecnico
        })

    df_normalizado = pd.DataFrame(registros)

    # 3. Guardar archivo Excel normalizado
    timestamp = obtener_timestamp_actual()
    nombre_archivo = f"OrdenesNormalizadas_{timestamp}.xlsx"
    ruta_guardado = os.path.join(directorio_destino, nombre_archivo)

    df_normalizado.to_excel(ruta_guardado, index=False)
    print(f"[+] Archivo de órdenes normalizado guardado en: {ruta_guardado} ({len(df_normalizado)} registros)")

    return ruta_guardado, df_normalizado


if __name__ == "__main__":
    import glob
    archivos = sorted(glob.glob("Documentos/Ordenes/*.xlsx"))
    if archivos:
        normalizar_registro_ordenes(archivos[-1])
    else:
        print("No se encontraron archivos en Documentos/Ordenes/")
