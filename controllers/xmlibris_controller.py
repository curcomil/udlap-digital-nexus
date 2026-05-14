from flask import Response
from db import MongoDBConnection_XMLibris
import json
from bson import ObjectId
import re
import unicodedata
from datetime import datetime, timezone


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
    result = db.get_all_carpetas()
    status = result.pop("status", 500)
    return Response(json.dumps(result, default=str), mimetype="application/json"), status


def get_items_by_carpeta_id(coleccion: str, carpeta_id: ObjectId):
    db = MongoDBConnection_XMLibris(coleccion)
    result = db.get_items_by_carpeta_id(carpeta_id)
    status = result.pop("status", 500)
    return Response(json.dumps(result, default=str), mimetype="application/json"), status


def get_carpeta_by_id(coleccion: str, carpeta_id: ObjectId):
    db = MongoDBConnection_XMLibris(coleccion)
    result = db.get_carpeta_by_id(ObjectId(carpeta_id))
    status = result.pop("status", 500)
    return Response(json.dumps(result, default=str), mimetype="application/json"), status


def actualizar_carpeta(coleccion: str, carpeta_id: ObjectId, data: dict):
    db = MongoDBConnection_XMLibris(coleccion)
    result = db.update_carpeta(ObjectId(carpeta_id), data)
    status = result.pop("status", 500)
    return Response(json.dumps(result, default=str), mimetype="application/json"), status


def actulizar_item(coleccion: str, item_id: ObjectId, data: dict):
    db = MongoDBConnection_XMLibris(coleccion)
    result = db.update_item(ObjectId(item_id), data)
    status = result.pop("status", 500)
    return Response(json.dumps(result, default=str), mimetype="application/json"), status


def search_by_filter(coleccion: str, data: dict):
    db = MongoDBConnection_XMLibris(coleccion)
    if data.get("filtro") == "nombre_expediente_normalizado":
        data["query"] = normalizar_setspec(data.get("query"))
    result = db.search_by_filters(data)
    status = result.pop("status", 500)
    return Response(json.dumps(result, default=str), mimetype="application/json"), status


def new_collection_controller(
    new_collection: str, new_collection_data: dict, submitted_user_data: dict
):
    mongo = MongoDBConnection_XMLibris(new_collection)
    new_collection_schema = {
        "type": "collection",
        "ref_collection": new_collection,
        "payload": new_collection_data,
        "status": "pending_coordinator",
        "reviewedByCoordinator": {},
        "coordinatorReviewedAt": "",
        "chiefReviewedAt": "",
        "rejectedTo": "",
        "rejectedBy": "",
        "rejectNote": "",
        "history": [
            {
                "action": "create",
                "by": submitted_user_data,
                "date": datetime.now(timezone.utc),
                "note": "",
            }
        ],
    }
    result = mongo.new_collection(data=new_collection_data)
    status = result.pop("status", 500)
    return Response(json.dumps(result, default=str), mimetype="application/json"), status
