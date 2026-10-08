import requests
from bs4 import BeautifulSoup

from config import URL_LOGIN, DEFAULT_USERNAME, DEFAULT_PASSWORD, DEFAULT_HEADERS
from Utils.utilsScrapper import extraer_tokens_aspnet, resolver_form_action

def login(usuario: str = DEFAULT_USERNAME, password: str = DEFAULT_PASSWORD) -> tuple[bool, requests.Session]:
    """
    Inicia sesión en la plataforma ScordSoft y retorna una tupla (éxito, sesión).
    Reutiliza la instancia Session con cookies y headers configurados.
    """
    session = requests.Session()
    session.headers.update(DEFAULT_HEADERS)

    print(f"[*] Obteniendo página de login: {URL_LOGIN}")
    response_get = session.get(URL_LOGIN)
    response_get.raise_for_status()

    soup = BeautifulSoup(response_get.text, "html.parser")
    action_url = resolver_form_action(soup, URL_LOGIN)

    # Extraer tokens estándar de ASP.NET
    tokens = extraer_tokens_aspnet(soup)

    # Preparar el payload del login
    payload = {
        **tokens,
        "ctl00$txtUsuario": usuario,
        "ctl00$txtClave": password,
        "ctl00$btnIngresar": "Ingresar"
    }

    headers_post = {
        "Origin": URL_LOGIN.rstrip("/"),
        "Referer": URL_LOGIN,
        "Content-Type": "application/x-www-form-urlencoded"
    }

    print("[*] Enviando credenciales al servidor...")
    response_post = session.post(action_url, data=payload, headers=headers_post, allow_redirects=True)
    response_post.raise_for_status()

    soup_post = BeautifulSoup(response_post.text, "html.parser")

    # Verificar si el backend retornó un mensaje de error
    lbl_error = soup_post.find(id="ctl00_lblMsjError")
    error_msg = lbl_error.get_text(strip=True) if lbl_error else ""

    is_still_login = soup_post.find("input", id="ctl00_txtUsuario") is not None

    if error_msg:
        print(f"[-] Error en el login: {error_msg}")
        return False, session
    elif not is_still_login or "Default.aspx" in response_post.url:
        print("[+] ¡Login exitoso!")
        return True, session
    else:
        print("[?] Estado de login no concluyente.")
        return False, session

if __name__ == "__main__":
    exito, sesion = login()
    print("Resultado login:", exito)
