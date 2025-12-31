import json
import unicodedata
import re
from datetime import datetime

def normalizar_setspec(texto: str) -> str:
    """
    Convierte texto humano en setSpec válido OAI
    """
    texto = texto.lower()
    texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")
    texto = re.sub(r"[^a-z0-9]+", "_", texto)
    return texto.strip("_")


def generar_listsets_oai(ruta_json: str, base_url: str) -> str:
    with open(ruta_json, "r", encoding="utf-8") as f:
        data = json.load(f)

    response_date = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    xml = []
    xml.append('<?xml version="1.0" encoding="UTF-8"?>')
    xml.append(
        '<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/" '
        'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
        'xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/ '
        'http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd">'
    )

    xml.append(f"<responseDate>{response_date}</responseDate>")
    xml.append(f'<request verb="ListSets">{base_url}</request>')
    xml.append("<ListSets>")

    for coleccion in data:
        nombre_col = coleccion["coleccion"]
        col_spec = normalizar_setspec(nombre_col)

        # Set padre
        xml.append("<set>")
        xml.append(f"<setSpec>{col_spec}</setSpec>")
        xml.append(f"<setName>{nombre_col}</setName>")
        xml.append("</set>")

        # Subcolecciones
        for sub in coleccion.get("subcolecciones", []):
            sub_spec = normalizar_setspec(sub)
            xml.append("<set>")
            xml.append(f"<setSpec>{col_spec}:{sub_spec}</setSpec>")
            xml.append(f"<setName>{sub}</setName>")
            xml.append("</set>")

    xml.append("</ListSets>")
    xml.append("</OAI-PMH>")

    return "\n".join(xml)

