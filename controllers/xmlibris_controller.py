from flask import Response
from db import MongoDBConnection_XMLibris
import json
from bson import ObjectId
import re
import unicodedata


def normalizar_setspec(texto: str) -> str:
    if not texto:
        return ""

    texto = texto.lower()
    texto = (
        unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")
    )
    texto = re.sub(r"[^a-z0-9]+", "_", texto)
    return texto.strip("_")


def get_all_carpetas(coleccion: str):
    db = MongoDBConnection_XMLibris(coleccion)
    carpetas = db.get_all_carpetas()
    return Response(json.dumps(carpetas, default=str), mimetype="application/json")


def get_items_by_carpeta_id(coleccion: str, carpeta_id: ObjectId):
    db = MongoDBConnection_XMLibris(coleccion)
    items = db.get_items_by_carpeta_id(carpeta_id)
    return Response(json.dumps(items, default=str), mimetype="application/json")


def get_carpeta_by_id(coleccion: str, carpeta_id: ObjectId):
    db = MongoDBConnection_XMLibris(coleccion)
    carpeta = db.get_carpeta_by_id(ObjectId(carpeta_id))
    if carpeta:
        return Response(json.dumps(carpeta, default=str), mimetype="application/json")
    else:
        return (
            Response(
                json.dumps({"message": "Carpeta no encontrada"}),
                mimetype="application/json",
            ),
            404,
        )


def actualizar_carpeta(coleccion: str, carpeta_id: ObjectId, data: dict):
    db = MongoDBConnection_XMLibris(coleccion)
    result = db.update_carpeta(ObjectId(carpeta_id), data)
    if not result:
        return (
            Response(
                json.dumps({"message": "Carpeta no encontrada o sin cambios"}),
                mimetype="application/json",
            ),
            404,
        )
    return Response(
        json.dumps(
            {"message": "Carpeta actualizada exitosamente", "carpeta": result},
            default=str,
        ),
        mimetype="application/json",
    )


def actulizar_item(coleccion: str, item_id: ObjectId, data: dict):
    db = MongoDBConnection_XMLibris(coleccion)
    result = db.update_item(ObjectId(item_id), data)
    if not result:
        return (
            Response(
                json.dumps({"message": "Item no encontrado o sin cambios"}),
                mimetype="application/json",
            ),
            404,
        )
    return Response(
        json.dumps(
            {"message": "Item actualizado exitosamente", "item": result},
            default=str,
        ),
        mimetype="application/json",
    )


def search_by_filter(coleccion: str, data: dict):
    db = MongoDBConnection_XMLibris(coleccion)
    if data.get("filtro") == "nombre_expediente_normalizado":
        data["query"] = normalizar_setspec(data.get("query"))
    result = db.search_by_filters(data)
    if not result:
        return (
            Response(
                json.dumps({"message": "Sin coincidencias", "resultado": []}),
                mimetype="application/json",
            ),
            404,
        )
    return Response(
        json.dumps(
            {"message": "Búsqueda exitosa", "resultado": result},
            default=str,
        ),
        mimetype="application/json",
    )
