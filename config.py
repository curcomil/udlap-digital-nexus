"""Configuración transversal de la API.

El archivo estaba vacío y reservado para esto.
"""

import os


def cors_origins():
    """Orígenes permitidos por CORS.

    Se leen de `CORS_ORIGINS` (lista separada por comas). Si la variable no está
    definida se devuelve "*", que es el comportamiento histórico. En despliegue
    conviene fijarla a los orígenes reales del frontend.
    """
    origenes = os.getenv("CORS_ORIGINS")
    if not origenes:
        return "*"
    return [origen.strip() for origen in origenes.split(",") if origen.strip()]
