from flask import Response
from db import MongoDBConnection_XMLibris
import json
from bson import ObjectId


def get_all_carpetas():
    db = MongoDBConnection_XMLibris("amc")
    carpetas = db.get_all_carpetas()
    return Response(json.dumps(carpetas, default=str), mimetype="application/json")


def get_items_by_carpeta_id(carpeta_id: ObjectId):
    db = MongoDBConnection_XMLibris("amc")
    items = db.get_items_by_carpeta_id(carpeta_id)
    return Response(json.dumps(items, default=str), mimetype="application/json")


def get_carpeta_by_id(carpeta_id: ObjectId):
    db = MongoDBConnection_XMLibris("amc")
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


def actualizar_carpeta(carpeta_id: ObjectId, data: dict):
    db = MongoDBConnection_XMLibris("amc")
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
