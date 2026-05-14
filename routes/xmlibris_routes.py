import os
from flask import current_app as app
from flask_cors import CORS
from flask import Blueprint, request
from bson import ObjectId
from middlewares import require_coordinator
from controllers import (
    get_all_carpetas,
    get_items_by_carpeta_id,
    actualizar_carpeta,
    get_carpeta_by_id,
    actulizar_item,
    search_by_filter,
    new_collection_controller,
)

xmlibris_bp = Blueprint("xmlibris", __name__)
CORS(xmlibris_bp, origins="*")


@xmlibris_bp.route("/", methods=["GET"])
def xmlibris_root():
    if os.getenv("ENVIROMENT") == "debug":
        return {
            "message": "XMLibris root endpoint.",
            "available_endpoints": [
                {"path": "/amc", "description": "Colección Archivo Miguel Covarrubias"},
                {"path": "/newcollection", "method": "POST", "auth": "coordinator", "description": "Crear nueva colección"},
            ],
        }
    return {"message": "XMLibris endpoint."}


@xmlibris_bp.route("/amc", methods=["GET"])
def amc_root():
    if os.getenv("ENVIROMENT") == "debug":
        return {
            "message": "AMC root endpoint.",
            "available_endpoints": [
                {"path": "/amc/carpetas", "method": "GET"},
                {"path": "/amc/carpeta/<carpeta_id>", "method": "GET"},
                {"path": "/amc/carpeta/<carpeta_id>", "method": "PUT"},
                {"path": "/amc/items/<carpeta_id>", "method": "GET"},
                {"path": "/amc/item/<item_id>", "method": "PUT"},
                {"path": "/amc/findbyfilter", "method": "POST"},
            ],
        }
    return {"message": "AMC endpoint."}


@xmlibris_bp.route("/amc/carpetas", methods=["GET"])
def get_carpetas():
    return get_all_carpetas(coleccion="amc")


@xmlibris_bp.route("/amc/items/<carpeta_id>", methods=["GET"])
def get_items_by_carpeta(carpeta_id):
    if not ObjectId.is_valid(carpeta_id):
        return {"error": "ID inválido"}, 400

    return get_items_by_carpeta_id(coleccion="amc", carpeta_id=ObjectId(carpeta_id))


@xmlibris_bp.route("/amc/carpeta/<carpeta_id>", methods=["GET"])
def get_carpeta_by_id_route(carpeta_id):
    if not ObjectId.is_valid(carpeta_id):
        return {"error": "ID inválido"}, 400

    return get_carpeta_by_id(coleccion="amc", carpeta_id=ObjectId(carpeta_id))


@xmlibris_bp.route("/amc/carpeta/<carpeta_id>", methods=["PUT"])
def update_carpeta(carpeta_id):
    if not ObjectId.is_valid(carpeta_id):
        return {"error": "ID inválido"}, 400

    data = request.get_json()
    if not data:
        return {"error": "Datos JSON no proporcionados"}, 400

    return actualizar_carpeta(
        coleccion="amc", carpeta_id=ObjectId(carpeta_id), data=data
    )


@xmlibris_bp.route("/amc/item/<item_id>", methods=["PUT"])
def update_item(item_id):
    if not ObjectId.is_valid(item_id):
        return {"error": "ID inválido"}, 400

    data = request.get_json()
    if not data:
        return {"error": "Datos JSON no proporcionados"}, 400

    return actulizar_item(coleccion="amc", item_id=ObjectId(item_id), data=data)


@xmlibris_bp.route("/amc/findbyfilter", methods=["POST"])
def FindbyFilter():

    data = request.get_json()
    if not data:
        return {"error": "Filtros no proporcionados"}, 400

    return search_by_filter(coleccion="amc", data=data)


@xmlibris_bp.route("/newcollection", methods=["POST"])
@require_coordinator
def new_collection_route():
    data = request.get_json()
    if not data:
        return {"success": False, "message": "Datos JSON no proporcionados"}, 400

    submitted_user = data.pop("user", {})
    new_collection_name = data.pop("new_collection_name", "general")

    return new_collection_controller(
        new_collection=new_collection_name,
        submitted_user_data=submitted_user,
        new_collection_data=data,
    )
