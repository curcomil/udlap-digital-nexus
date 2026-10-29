import json
import logging
import os
import uuid

from flask import Response, jsonify, request, send_file

from db import MongoDBConnection_XMLibris
from datetime import datetime, timezone
from utils import generar_internal_id, limpiar_espacios_finales, normalizar_setspec
from scripts import (
    ErrorCargaArchivos,
    cargar_archivos_pendiente,
    eliminar_zip_subido,
)

logger = logging.getLogger(__name__)

_BUFFER_SUBIDA = 1024 * 1024

# Firmas válidas de un ZIP: archivo normal y archivo vacío.
_FIRMAS_ZIP = (b"PK\x03\x04", b"PK\x05\x06")


def get_all_subcolecciones(coleccion: str):
    db = MongoDBConnection_XMLibris("colecciones")
    result = db.get_all_subcolecciones(coleccion)
    status = result.pop("status", 500)
    return (
        Response(json.dumps(result, default=str), mimetype="application/json"),
        status,
    )


def get_all_collections(subcolecciones_filtro):
    db = MongoDBConnection_XMLibris("colecciones")
    result = db.get_all_collections(subcolecciones_filtro=subcolecciones_filtro)
    status = result.pop("status", 500)
    return (
        Response(json.dumps(result, default=str), mimetype="application/json"),
        status,
    )


def get_collection_by_internal_id(internal_id: str):
    db = MongoDBConnection_XMLibris("colecciones")
    result = db.get_collection_by_internal_id(internal_id)
    status = result.pop("status", 500)
    return (
        Response(json.dumps(result, default=str), mimetype="application/json"),
        status,
    )


def _ruta_portada(item: dict):
    metadata = item.get("metadata") or {}
    portada = metadata.get("portada")
    if not portada:
        return
    parents = item.get("parents") or {}
    coleccion = (parents.get("coleccion") or {}).get("setspec_collection")
    subcoleccion = (parents.get("subcoleccion") or {}).get("setspec_subcollection")
    internal_id = item.get("internal_id")
    if not (coleccion and subcoleccion and internal_id):
        return
    metadata["portada"] = f"{coleccion}/{subcoleccion}/{internal_id}/{portada}"


def get_items_by_subcoleccion(coleccion: str, subcoleccion: str):
    db = MongoDBConnection_XMLibris("items")
    result = db.get_items_by_subcoleccion(coleccion, subcoleccion)
    status = result.pop("status", 500)
    if result.get("success"):
        for item in result.get("data") or []:
            _ruta_portada(item)
    return (
        Response(json.dumps(result, default=str), mimetype="application/json"),
        status,
    )


def get_file(coleccion: str, subcoleccion: str, internal_id: str, archivo: str):
    result = MongoDBConnection_XMLibris.get_file_location(
        coleccion, subcoleccion, internal_id, archivo
    )
    status = result.pop("status", 500)
    if not result.get("success"):
        return (
            Response(json.dumps(result, default=str), mimetype="application/json"),
            status,
        )
    return send_file(result["data"]["ruta"], conditional=True), status


def actualizar_subcoleccion(coleccion: str, internal_id: str, data: dict):
    data = limpiar_espacios_finales(data)
    db = MongoDBConnection_XMLibris("colecciones")
    result = db.update_subcoleccion(coleccion, internal_id, data)
    status = result.pop("status", 500)
    return (
        Response(json.dumps(result, default=str), mimetype="application/json"),
        status,
    )


def actualizar_item(coleccion: str, internal_id: str, data: dict):
    data = limpiar_espacios_finales(data)
    db = MongoDBConnection_XMLibris("items")
    if isinstance(data.get("is_published"), str):
        data["is_published"] = data["is_published"].strip().lower() == "true"
    result = db.update_item(coleccion, internal_id, data)
    status = result.pop("status", 500)
    if result.get("success"):
        _ruta_portada(result.get("data") or {})
    return (
        Response(json.dumps(result, default=str), mimetype="application/json"),
        status,
    )


def get_campos_controller():
    db = MongoDBConnection_XMLibris("etiquetas")
    result = db.get_all_campos()
    status = result.pop("status", 500)
    return (
        Response(json.dumps(result, default=str), mimetype="application/json"),
        status,
    )


def new_collection_controller(new_collection_data: dict):
    db = MongoDBConnection_XMLibris("colecciones")
    data = {
        "coleccion": {
            "name_collection": new_collection_data.get("nombre_coleccion"),
            "setspec_collection": normalizar_setspec(
                new_collection_data.get("nombre_coleccion")
            ),
            "internal_id": generar_internal_id(),
        },
        "subcolecciones": [],
        "app": {"notas": "", "miniatura": "", "referencia_externa": ""},
        "status": "pending",
        "origen": new_collection_data.get("origen", None),
        "exportacion_fija": list(new_collection_data.get("exportacion_fija", [])),
        "schema": list(new_collection_data.get("schema", [])),
    }
    data = limpiar_espacios_finales(data)

    result = db.new_collection(data=data)
    status = result.pop("status", 500)
    return (
        Response(json.dumps(result, default=str), mimetype="application/json"),
        status,
    )


def new_subcollection_controller(new_subcollection_data: dict):
    db = MongoDBConnection_XMLibris("colecciones")
    data = {
        "name_subcollection": new_subcollection_data.get("nombre_subcoleccion"),
        "setspec_subcollection": normalizar_setspec(
            new_subcollection_data.get("nombre_subcoleccion")
        ),
        "internal_id": generar_internal_id(),
        "app": {"notas": "", "miniatura": "", "referencia_externa": ""},
        "status": "pending",
    }
    data = limpiar_espacios_finales(data)
    result = db.new_subcollection(
        data=data, internal_id=new_subcollection_data.get("coleccion_internal_id")
    )
    status = result.pop("status", 500)
    return (
        Response(json.dumps(result, default=str), mimetype="application/json"),
        status,
    )


def new_item(new_item_data: dict, files: list, libro: bool = False):

    origen = new_item_data.get("origen")
    if origen == "tesis":
        ruta_db = "items_tesis"
    else:
        ruta_db = "items"

    db = MongoDBConnection_XMLibris(ruta_db)

    parents = new_item_data.get("parents") or {}
    data = {
        "internal_id": generar_internal_id(),
        "status": "pending",
        "parents": parents,
        "metadata": new_item_data.get("metadata"),
        "app": {"notas": new_item_data.get("notas", "")},
    }

    ruta_archivos = {
        "coleccion": (parents.get("coleccion") or {}).get("setspec_collection"),
        "subcoleccion": (parents.get("subcoleccion") or {}).get(
            "setspec_subcollection"
        ),
        "internal_id": data.get("internal_id"),
    }

    zip_upload_id = new_item_data.get("zip_upload_id")

    try:
        data["content"] = cargar_archivos_pendiente(
            origen=origen,
            ruta=ruta_archivos,
            files=files,
            libro=libro,
            zip_upload_id=zip_upload_id,
        )
    except ErrorCargaArchivos as e:
        return (
            Response(
                json.dumps({"success": False, "message": e.message}, default=str),
                mimetype="application/json",
            ),
            e.status,
        )

    result = db.new_item(limpiar_espacios_finales(data))
    status = result.pop("status", 500)

    # El ZIP temporal se conserva si el insert falla, para poder reintentar el
    # alta sin volver a subir el archivo completo.
    if result.get("success") and libro and zip_upload_id:
        try:
            eliminar_zip_subido(zip_upload_id)
        except ErrorCargaArchivos as e:
            logger.warning(
                "No se pudo eliminar el ZIP temporal %s: %s",
                zip_upload_id,
                e.message,
            )

    return (
        Response(json.dumps(result, default=str), mimetype="application/json"),
        status,
    )


def subir_zip():
    """Guarda el ZIP recibido como cuerpo crudo y devuelve su ``upload_id``.

    Se escribe por bloques, sin pasar por el parser de multipart ni cargar el
    archivo en memoria. El ZIP queda en ``FILES_ROOT/tmp/<upload_id>.zip`` y el
    alta del item lo consume después con ``zip_upload_id``.
    """
    if request.mimetype == "multipart/form-data":
        return jsonify(
            {
                "success": False,
                "message": (
                    "Envía el ZIP como cuerpo crudo "
                    "(Content-Type: application/zip), no como multipart"
                ),
            }
        ), 400

    raiz = os.getenv("FILES_ROOT")
    if not raiz:
        return jsonify(
            {"success": False, "message": "FILES_ROOT no está configurado"}
        ), 500

    upload_id = uuid.uuid4().hex
    carpeta = os.path.join(os.path.abspath(raiz), "tmp")
    try:
        os.makedirs(carpeta, exist_ok=True)
    except OSError as exc:
        logger.exception("No se pudo preparar la carpeta temporal")
        return jsonify(
            {
                "success": False,
                "message": f"No se pudo preparar la carpeta temporal: {exc}",
            }
        ), 500

    destino = os.path.join(carpeta, f"{upload_id}.zip")
    escritos = 0

    try:
        with open(destino, "wb") as salida:
            primero = True
            while True:
                bloque = request.stream.read(_BUFFER_SUBIDA)
                if not bloque:
                    break

                if primero:
                    primero = False
                    if not bloque.startswith(_FIRMAS_ZIP):
                        raise ValueError("El archivo enviado no es un ZIP")

                escritos += len(bloque)
                salida.write(bloque)
    except ValueError as exc:
        if os.path.exists(destino):
            os.remove(destino)
        return jsonify({"success": False, "message": str(exc)}), 400
    except Exception:
        logger.exception("Error al guardar el ZIP subido")
        if os.path.exists(destino):
            os.remove(destino)
        return jsonify(
            {"success": False, "message": "Error al guardar el archivo"}
        ), 500

    if escritos == 0:
        os.remove(destino)
        return jsonify(
            {"success": False, "message": "No se recibió ningún archivo"}
        ), 400

    return jsonify(
        {
            "success": True,
            "message": "Archivo recibido",
            "status": 200,
            "data": {"upload_id": upload_id, "bytes": escritos},
        }
    ), 200
