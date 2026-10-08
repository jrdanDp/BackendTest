from bs4 import BeautifulSoup
from urllib.parse import urljoin

def extraer_input_valor(soup: BeautifulSoup, input_name: str, default: str = "") -> str:
    """
    Busca una etiqueta <input> por su atributo 'name' en el documento BeautifulSoup
    y retorna su valor (value). Si no existe, retorna el valor por defecto.
    """
    tag = soup.find("input", {"name": input_name})
    return tag.get("value", default) if tag else default

def extraer_tokens_aspnet(soup: BeautifulSoup) -> dict:
    """
    Extrae los campos ocultos estándar de control de estado de ASP.NET WebForms:
    - __VIEWSTATE
    - __VIEWSTATEGENERATOR
    - __EVENTVALIDATION
    - __EVENTTARGET
    - __EVENTARGUMENT
    - __LASTFOCUS
    """
    return {
        "__VIEWSTATE": extraer_input_valor(soup, "__VIEWSTATE"),
        "__VIEWSTATEGENERATOR": extraer_input_valor(soup, "__VIEWSTATEGENERATOR"),
        "__EVENTVALIDATION": extraer_input_valor(soup, "__EVENTVALIDATION"),
        "__EVENTTARGET": extraer_input_valor(soup, "__EVENTTARGET", ""),
        "__EVENTARGUMENT": extraer_input_valor(soup, "__EVENTARGUMENT", ""),
        "__LASTFOCUS": extraer_input_valor(soup, "__LASTFOCUS", "")
    }

def resolver_form_action(soup: BeautifulSoup, url_base: str, form_id: str = "aspnetForm") -> str:
    """
    Obtiene la URL absoluta a la que apunta el 'action' de un formulario específico.
    """
    form = soup.find("form", id=form_id) or soup.find("form")
    if form and form.get("action"):
        return urljoin(url_base, form.get("action"))
    return url_base
