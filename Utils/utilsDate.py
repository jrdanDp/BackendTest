from datetime import datetime

DATE_FORMAT_WEB = "%d/%m/%Y"
TIMESTAMP_FORMAT = "%Y%m%d_%H%M%S"

def obtener_fecha_hoy_str(fmt=DATE_FORMAT_WEB):
    """Retorna la fecha actual como string con formato por defecto DD/MM/YYYY."""
    return datetime.today().strftime(fmt)

def obtener_primer_dia_mes_str(fmt=DATE_FORMAT_WEB):
    """Retorna el primer día del mes actual como string en formato DD/MM/YYYY."""
    return datetime.today().replace(day=1).strftime(fmt)

def obtener_timestamp_actual(fmt=TIMESTAMP_FORMAT):
    """Retorna la fecha y hora actual en formato apto para nombres de archivo."""
    return datetime.now().strftime(fmt)

def validar_rango_fechas(fecha_inicial_str, fecha_final_str, fmt=DATE_FORMAT_WEB):
    """
    Valida que ambas fechas cumplan el formato esperado y que
    fecha_inicial no sea superior a fecha_final.

    Retorna una tupla de objetos (datetime_ini, datetime_fin).
    """
    try:
        f_ini = datetime.strptime(fecha_inicial_str, fmt)
        f_fin = datetime.strptime(fecha_final_str, fmt)
    except ValueError as e:
        raise ValueError(
            f"Formato de fecha inválido. Se espera {fmt} (ej: 10/09/2026). Detalle: {e}"
        )

    if f_ini > f_fin:
        raise ValueError(
            f"Error de validación: La fechaInicial ({fecha_inicial_str}) no puede ser superior "
            f"a la fechaFinal ({fecha_final_str})."
        )

    return f_ini, f_fin
