import re
from thefuzz import fuzz, process

COBRADORES_OFICIALES = ["MARIA", "FATIMA", "EDWIN", "CALL CENTER"]
ALIASES_COBRADOR = {
    "CC": "CALL CENTER"
}

METODOS_OFICIALES = [
    "EFECTIVO",
    "DEP BANCO DE CREDITO YAPE",
    "DEP BANCO DE CREDITO IZIPAY",
    "DEP BANCO DE CREDITO TRANSFERENCIA",
    "DEP BANCO DE CREDITO AGENTE BCP",
    "DEP BANCO CONTINENTAL YAPE",
    "DEP BANCO CONTINENTAL IZIPAY",
    "DEP BANCO CONTINENTAL TRANSFERENCIA",
    "DEP BANCO FINANCIERO YAPE",
    "DEP BANCO FINANCIERO IZIPAY",
    "DEP BANCO FINANCIERO TRANSFERENCIA",
]

UMBRAL_COBRADOR = 75
UMBRAL_CONFIANZA_METODO = 80

def normalizar_texto(texto: str) -> str:
    """Limpia espacios redundantes y pasa a mayúsculas."""
    if not texto:
        return ""
    return re.sub(r"\s+", " ", str(texto)).strip().upper()

def separar_referencia(referencia_raw: str) -> tuple[str, str]:
    """
    Separa el campo 'Referencias' en (METODO_PAGO, RESPONSABLE).

    Lógica:
    1. Si la referencia está vacía o es NaN -> (PENDIENTE REVISION, OFICINA).
    2. Busca primero al responsable:
       a) Si coincide con un alias directo (ej: token final 'CC' -> CALL CENTER).
       b) Por similitud con COBRADORES_OFICIALES en tokens o cadenas.
       c) Si no se detecta ningún patrón de responsable -> RESPONSABLE = 'OFICINA'.
       d) Si parece haber responsable pero no supera el UMBRAL_COBRADOR -> RESPONSABLE = 'POR DETERMINAR'.
    3. Remueve el responsable identificado del texto para aislar el método de pago.
    4. Compara el texto residual contra METODOS_OFICIALES usando fuzz.ratio/partial_ratio:
       a) Si supera UMBRAL_CONFIANZA_METODO -> Asigna el método oficial.
       b) Si no supera -> 'PENDIENTE REVISION'.
    """
    texto = normalizar_texto(referencia_raw)
    if not texto or texto == "NAN":
        return "PENDIENTE REVISION", "OFICINA"

    tokens = texto.split(" ")
    responsable_detectado = None
    texto_sin_responsable = texto

    # 1. Revisar si el último token es un alias conocido (ej. 'CC')
    ultimo_token = tokens[-1]
    if ultimo_token in ALIASES_COBRADOR:
        responsable_detectado = ALIASES_COBRADOR[ultimo_token]
        # Remover el alias del texto
        texto_sin_responsable = " ".join(tokens[:-1]).strip()
    else:
        # 2. Buscar si el último token o subcadena se parece a algún cobrador oficial
        # Primero probamos con el último token (que es típicamente donde va el nombre)
        mejor_cobrador, score_token = process.extractOne(
            ultimo_token,
            COBRADORES_OFICIALES,
            scorer=fuzz.ratio
        ) if ultimo_token else (None, 0)

        if score_token >= UMBRAL_COBRADOR:
            responsable_detectado = mejor_cobrador
            texto_sin_responsable = " ".join(tokens[:-1]).strip()
        else:
            # Probar si alguna palabra del texto coincide con los cobradores
            candidato_encontrado = None
            pos_candidato = -1
            for i, tok in enumerate(tokens):
                cob_match, sc = process.extractOne(tok, COBRADORES_OFICIALES, scorer=fuzz.ratio)
                if sc >= UMBRAL_COBRADOR:
                    candidato_encontrado = cob_match
                    pos_candidato = i
                    break

            if candidato_encontrado:
                responsable_detectado = candidato_encontrado
                # Remover ese token específico
                tokens_limpios = [t for j, t in enumerate(tokens) if j != pos_candidato]
                texto_sin_responsable = " ".join(tokens_limpios).strip()

    # Si no se detectó responsable, determinar si es OFICINA o POR DETERMINAR
    if not responsable_detectado:
        # Si el texto residual coincide casi exactamente con un método oficial,
        # significa que nunca hubo cobrador en el texto -> Pertenece a OFICINA
        mejor_m, score_m = process.extractOne(texto, METODOS_OFICIALES, scorer=fuzz.ratio)
        if score_m >= UMBRAL_CONFIANZA_METODO:
            responsable_detectado = "OFICINA"
            texto_sin_responsable = texto
        else:
            # Hay palabras extras o no reconocidas que no pasaron el umbral
            responsable_detectado = "POR DETERMINAR"

    # 3. Normalizar el método de pago con el texto libre de cobrador
    if not texto_sin_responsable:
        metodo_pago_detectado = "PENDIENTE REVISION"
    else:
        mejor_metodo, score_metodo = process.extractOne(
            texto_sin_responsable,
            METODOS_OFICIALES,
            scorer=fuzz.ratio
        )
        if score_metodo >= UMBRAL_CONFIANZA_METODO:
            metodo_pago_detectado = mejor_metodo
        else:
            # Intentar con partial_ratio como salvaguarda
            mejor_metodo_p, score_p = process.extractOne(
                texto_sin_responsable,
                METODOS_OFICIALES,
                scorer=fuzz.partial_ratio
            )
            if score_p >= 80:
                metodo_pago_detectado = mejor_metodo_p
            else:
                metodo_pago_detectado = "PENDIENTE REVISION"

    return metodo_pago_detectado, responsable_detectado
