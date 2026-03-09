from flask import current_app as app
from flask_cors import CORS
from flask import Blueprint, request
from bson import ObjectId
from controllers import (
    get_all_carpetas,
    get_items_by_carpeta_id,
    actualizar_carpeta,
    get_carpeta_by_id,
    actulizar_item,
    search_by_filter,
)

xmlibris_bp = Blueprint("xmlibris", __name__)
CORS(xmlibris_bp, origins="*")


@xmlibris_bp.route("/", methods=["GET"])
def xmlibris_root():
    return {"message": "xmlibris root endpoint", "avalible_endpoints": ["/amc"]}


@xmlibris_bp.route("/amc", methods=["GET"])
def amc_root():
    return {
        "message": "AMC root endpoint.",
        "available_endpoints": [
            "/carpetas",
            "/carpeta/<carpeta_id>",
            "/items",
            "/items/<carpeta_id>",
        ],
    }


@xmlibris_bp.route("/amc/carpetas", methods=["GET"])
def get_carpetas():
    return get_all_carpetas()


@xmlibris_bp.route("/amc/items/<carpeta_id>", methods=["GET"])
def get_items_by_carpeta(carpeta_id):
    if not ObjectId.is_valid(carpeta_id):
        return {"error": "ID inválido"}, 400

    return get_items_by_carpeta_id(ObjectId(carpeta_id))


@xmlibris_bp.route("/amc/carpeta/<carpeta_id>", methods=["PUT"])
def update_carpeta(carpeta_id):
    if not ObjectId.is_valid(carpeta_id):
        return {"error": "ID inválido"}, 400

    data = request.get_json()
    if not data:
        return {"error": "Datos JSON no proporcionados"}, 400

    return actualizar_carpeta(ObjectId(carpeta_id), data)


@xmlibris_bp.route("/amc/carpeta/<carpeta_id>", methods=["GET"])
def get_carpeta_by_id_route(carpeta_id):
    if not ObjectId.is_valid(carpeta_id):
        return {"error": "ID inválido"}, 400

    return get_carpeta_by_id(ObjectId(carpeta_id))


@xmlibris_bp.route("/amc/item/<item_id>", methods=["PUT"])
def update_item(item_id):
    if not ObjectId.is_valid(item_id):
        return {"error": "ID inválido"}, 400

    data = request.get_json()
    if not data:
        return {"error": "Datos JSON no proporcionados"}, 400

    return actulizar_item(ObjectId(item_id), data)


@xmlibris_bp.route("/amc/findbyfilter", methods=["POST"])
def FindbyFilter():

    data = request.get_json()
    if not data:
        return {"error": "Filtros no proporcionados"}, 400

    return search_by_filter(data)
