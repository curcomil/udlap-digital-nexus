import random
import re
import time
import unicodedata


def generar_internal_id() -> str:
    """Genera un id interno único a partir de azar + timestamp en milisegundos."""
    return f"{random.randint(100000, 999999)}{int(time.time()*1000)}"


def normalizar_setspec(texto: str) -> str:
    """Normaliza un texto para usarlo como setSpec: minúsculas, sin acentos
    ni caracteres especiales, separando con guion bajo."""
    if not texto:
        return ""

    texto = texto.lower()
    texto = (
        unicodedata.normalize("NFKD", texto)
        .encode("ascii", "ignore")
        .decode("ascii")
    )
    texto = re.sub(r"[^a-z0-9]+", "_", texto)
    return texto.strip("_")


def limpiar_espacios_finales(valor, caracteres=None):
    """Quita caracteres al final de cada string, por defecto espacios.

    Recorre diccionarios, listas y tuplas. No modifica las claves de los
    diccionarios ni los valores que no sean strings (ObjectId, datetime,
    booleanos, números, etc.).

    ``caracteres`` funciona como en ``str.rstrip``: si es ``None`` se quitan
    espacios, tabs y saltos de línea; si se pasa un string, se quitan esos
    caracteres.
    """
    if isinstance(valor, str):
        return valor.rstrip(caracteres)
    if isinstance(valor, dict):
        return {
            clave: limpiar_espacios_finales(contenido, caracteres)
            for clave, contenido in valor.items()
        }
    if isinstance(valor, list):
        return [
            limpiar_espacios_finales(contenido, caracteres)
            for contenido in valor
        ]
    if isinstance(valor, tuple):
        return tuple(
            limpiar_espacios_finales(contenido, caracteres)
            for contenido in valor
        )
    return valor
