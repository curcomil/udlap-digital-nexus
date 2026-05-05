"""
Route: /mets/run
Lanza la generación de METS AIP en un hilo background y responde
inmediatamente con OK o error.

Parámetro GET:
    set  - setspec de la colección, opcionalmente con subcolección separada
           por ":" igual que en OAI-PMH ListSets.

Ejemplos:
    Colección completa:   GET /mets/run?set=archivo_historico_de_la_provincia_...
    Una subcolección:     GET /mets/run?set=archivo_historico_...:documentos

Flujo interno:
    setfilter(set) → [col_name] o [col_name, sub_name]
    find_items(col_name, sub_name) → lista de items del acervo
    create_mets(...)  → tar.gz en output/{set}/
"""

import traceback
import threading
from flask import Blueprint, request
from db import MongoDBConnection_OAI
from utils import setfilter
from controllers import create_mets

mets_bp = Blueprint("mets", __name__, url_prefix="/mets")

repo_items_acervo = MongoDBConnection_OAI("items")


def _run_mets_job(set_param: str, col_name: str, sub_name: str | None) -> None:
    """Corre en background: recupera items y genera el tar.gz."""
    try:
        # 1. Recuperar items — find_items ya acepta sub_name=None para toda la colección
        items = repo_items_acervo.find_items(col_name, sub_name)

        if not items:
            print(f"[METS] ⚠  Sin items para set='{set_param}'")
            return

        print(f"[METS] {len(items)} items encontrados para set='{set_param}'")

        # 2. Recuperar estructura de la colección desde Mongo (para IDs y subcolecciones)
        repo_estructura = MongoDBConnection_OAI("estructura")
        col_structure = repo_estructura.collection.find_one(
            {"coleccion.name_collection": col_name}, {"_id": 0}
        )

        if not col_structure:
            # Fallback: estructura mínima inferida del set_param
            prefijo = set_param.split(":")[0]
            print(
                f"[METS] ⚠  Estructura no encontrada para '{col_name}', usando inferida"
            )
            col_structure = {
                "coleccion": {
                    "name_collection": col_name,
                    "setspec_collection": prefijo,
                },
                "subcolecciones": [],
            }

        # 3. Generar — set_param como nombre de carpeta y archivo de salida
        result = create_mets(
            items=items,
            col_structure=col_structure,
            col_name=col_name,
            set_spec=set_param,
        )

        print(f"[METS] ✅ Job finalizado: {result}")

    except Exception as e:
        print(f"[METS] ❌ Error crítico — set='{set_param}': {e}")
        traceback.print_exc()


@mets_bp.route("/run", methods=["GET"])
def mets_run():
    """
    GET /mets/run?set=<setspec>

    Responde 202 inmediatamente y lanza la generación en background.
    El progreso se puede seguir en la consola del servidor.
    """
    set_param = request.args.get("set", "").strip()

    if not set_param:
        return {"error": "Missing required parameter: set"}, 400

    # setfilter resuelve el setspec contra Mongo y devuelve nombres legibles
    filtros = setfilter(set_param)

    if not filtros:
        return {
            "error": f"Set '{set_param}' no encontrado en la estructura de colecciones"
        }, 404

    col_name = filtros[0]
    sub_name = filtros[1] if len(filtros) > 1 else None

    # Lanzar job en background
    job = threading.Thread(
        target=_run_mets_job,
        args=(set_param, col_name, sub_name),
        daemon=True,
        name=f"mets-{set_param[:40]}",
    )
    job.start()

    print(
        f"[METS] 🚀 Job iniciado — col='{col_name}'"
        + (f" sub='{sub_name}'" if sub_name else " (colección completa)")
    )

    return {
        "status": "ok",
        "message": "Generación de METS AIP iniciada en background",
        "set": set_param,
        "coleccion": col_name,
        **({"subcoleccion": sub_name} if sub_name else {}),
    }, 202
