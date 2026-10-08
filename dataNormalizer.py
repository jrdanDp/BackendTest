import os
import pandas as pd
import numpy as np

from config import DIR_REGISTRO_NORMALIZADOS
from Utils.utilsFiles import asegurar_directorio
from Utils.utilsNormalizer import separar_referencia

# Columnas clave e indispensables de la venta a conservar en el archivo final
COLUMNAS_VENTA_INTERES = [
    "Tipo",
    "ABONADO",
    "Precio Venta",
    "Estado",
    "F. PAGO",
    "HORA ING",
    "METODO_PAGO",
    "RESPONSABLE"
]

def formatear_abonado(valor) -> int | None:
    """
    Convierte el valor de ABONADO (ej: '00002712', 2712.0) a entero estricto (2712).
    Elimina los ceros a la izquierda y evita decimales.
    """
    if pd.isna(valor):
        return None
    try:
        # Primero convertir a float para manejar casos como '2712.0' o floats
        val_float = float(valor)
        return int(val_float)
    except (ValueError, TypeError):
        # Si tiene caracteres no numéricos, extraer sólo los dígitos
        digitos = "".join(ch for ch in str(valor) if ch.isdigit())
        return int(digitos) if digitos else None

def formatear_fecha_pago(valor) -> str:
    """
    Garantiza el formato DD/MM/YYYY para la fecha de pago.
    """
    if pd.isna(valor):
        return ""
    try:
        # Intentar parsear con pandas to_datetime
        ts = pd.to_datetime(valor, dayfirst=True)
        return ts.strftime("%d/%m/%Y")
    except Exception:
        return str(valor).strip()

def formatear_hora_ing(valor) -> str:
    """
    Garantiza el formato HH:MM para la hora de ingreso.
    """
    if pd.isna(valor):
        return ""
    try:
        # Si viene como objeto datetime o time
        if hasattr(valor, "strftime"):
            return valor.strftime("%H:%M")
        ts = pd.to_datetime(str(valor).strip())
        return ts.strftime("%H:%M")
    except Exception:
        # Si ya viene en formato de texto '10:03' o '10:03:00'
        partes = str(valor).strip().split(":")
        if len(partes) >= 2:
            return f"{partes[0].zfill(2)}:{partes[1].zfill(2)}"
        return str(valor).strip()

def normalizar_registro_cobros(
    ruta_archivo_origen: str,
    directorio_salida: str = DIR_REGISTRO_NORMALIZADOS
) -> str:
    """
    Lee el archivo Excel descargado, detecta la fila real de cabecera,
    aplica las transformaciones requeridas:
    - ABONADO: Entero estricto sin ceros iniciales ni decimales (ej: 2712).
    - F. PAGO: Formato DD/MM/YYYY.
    - HORA ING: Formato HH:MM.
    - Referencias: Separada en METODO_PAGO y RESPONSABLE por similitud.
    - Filtra y reordena solo las columnas clave de venta seleccionadas.
    
    Guarda el archivo normalizado en directorio_salida y retorna su ruta.
    """
    if not os.path.exists(ruta_archivo_origen):
        raise FileNotFoundError(f"No se encontró el archivo origen: {ruta_archivo_origen}")

    print(f"[*] Leyendo archivo para normalización: {ruta_archivo_origen}")
    df_raw = pd.read_excel(ruta_archivo_origen, header=None)

    # 1. Detectar dinámicamente la fila de cabecera
    header_idx = 4

    print(f"[*] Cabecera identificada en la fila {header_idx}")

    # Extraer columnas y datos
    columnas_originales = [str(c).strip() if pd.notna(c) else f"Columna_{i}" for i, c in enumerate(df_raw.iloc[header_idx])]
    df = df_raw.iloc[header_idx + 1:].copy()
    df.columns = columnas_originales

    # Eliminar filas de totales o vacías
    primera_col = df.columns[0]
    df = df[df[primera_col].notna()]
    df = df[~df[primera_col].astype(str).str.contains("Total", case=False, na=False)]

    # Mapeo de nombres de columna para estandarizar accesos
    col_map = {c.strip().upper(): c for c in df.columns}

    # 2. Normalización de ABONADO (Entero puro)
    col_abonado = col_map.get("ABONADO")
    if col_abonado:
        print("[*] Normalizando columna ABONADO a entero...")
        df["ABONADO"] = df[col_abonado].apply(formatear_abonado).astype("Int64")

    # 3. Normalización de F. Pago y Hora Ing
    col_fpago = col_map.get("F. PAGO") or col_map.get("FECHA PAGO")
    if col_fpago:
        print("[*] Formateando columna F. PAGO a día/mes/año...")
        df["F. PAGO"] = df[col_fpago].apply(formatear_fecha_pago)

    col_hora = col_map.get("HORA ING") or col_map.get("HORA INGRESO")
    if col_hora:
        print("[*] Formateando columna HORA ING a hora:minuto...")
        df["HORA ING"] = df[col_hora].apply(formatear_hora_ing)

    # 4. Separación de Referencias en METODO_PAGO y RESPONSABLE por similitud
    col_referencias = col_map.get("REFERENCIAS") or col_map.get("REFERENCIA")
    if col_referencias:
        print("[*] Separando Referencias en METODO_PAGO y RESPONSABLE...")
        resultados_separacion = df[col_referencias].apply(separar_referencia)
        df["METODO_PAGO"] = [r[0] for r in resultados_separacion]
        df["RESPONSABLE"] = [r[1] for r in resultados_separacion]
    else:
        df["METODO_PAGO"] = "PENDIENTE REVISION"
        df["RESPONSABLE"] = "OFICINA"

    # 5. Filtrar y ordenar las columnas seleccionadas
    columnas_finales = [c for c in COLUMNAS_VENTA_INTERES if c in df.columns]
    df_resultado = df[columnas_finales].copy()

    # 6. Guardar archivo normalizado en Documentos/RegistroCobrosNormalizados
    asegurar_directorio(directorio_salida)
    nombre_base = os.path.basename(ruta_archivo_origen)
    nombre_sin_ext, ext = os.path.splitext(nombre_base)
    nombre_normalizado = f"{nombre_sin_ext}_Normalizado{ext}"
    ruta_salida = os.path.join(directorio_salida, nombre_normalizado)

    df_resultado.to_excel(ruta_salida, index=False)
    print(f"[+] Archivo normalizado generado: {ruta_salida} ({len(df_resultado)} registros procesados)")

    return ruta_salida

if __name__ == "__main__":
    import glob
    archivos = glob.glob("Documentos/RegistroCobros/*.xlsx")
    if archivos:
        normalizar_registro_cobros(archivos[-1])
