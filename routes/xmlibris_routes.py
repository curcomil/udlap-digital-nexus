import os
from flask_cors import CORS
from flask import Blueprint, request
from config import cors_origins
from middlewares import (
    require_coordinator,
    require_roles,
    NuevaColeccionSchema,
    NuevaSubcoleccionSchema,
    validar_con,
    validar_schema,
)
from utils import get_debug_docs
from controllers import (
    get_all_subcolecciones,
    get_items_by_subcoleccion,
    get_file,
    actualizar_subcoleccion,
    actualizar_item,
    new_collection_controller,
    get_all_collections,
    get_collection_by_internal_id,
    get_campos_controller,
    new_subcollection_controller,
    new_item,
    subir_zip,
)

xmlibris_bp = Blueprint("xmlibris", __name__)
CORS(xmlibris_bp, origins=cors_origins())


# Roles con permiso para crear y modificar recursos
ROLES_ESCRITURA = ("admin", "coordinator", "digitizer")


# ============== Peticiones GET ==============
# Devuelve la información base del blueprint XMLibris.
# En modo debug responde con la documentación del módulo, si no con un mensaje simple.
@xmlibris_bp.route("/", methods=["GET"])
def xmlibris_root():
    if os.getenv("ENVIROMENT") == "debug":
        return get_debug_docs("xmlibris")
    return {"message": "XMLibris endpoint."}


# ------------------------------
# Devuelve la información base de una colección específica.
# Recibe el nombre de la colección en la URL (<coleccion>).
@xmlibris_bp.route("/<coleccion>", methods=["GET"])
def coleccion_root(coleccion):
    if os.getenv("ENVIROMENT") == "debug":
        return get_debug_docs("coleccion", coleccion=coleccion)
    return {"message": f"{coleccion} endpoint."}


# ------------------------------
# Devuelve todas las subcolecciones de una colección.
# Recibe el nombre de la colección en la URL (<coleccion>).
@xmlibris_bp.route("/<coleccion>/subcolecciones", methods=["GET"])
def get_subcolecciones(coleccion):
    return get_all_subcolecciones(coleccion=coleccion)


# ------------------------------
# Devuelve todos los ítems de una subcolección dentro de una colección.
# Recibe la colección y la subcolección en la URL.
@xmlibris_bp.route("/<coleccion>/items/<subcoleccion>", methods=["GET"])
def get_items_by_subcoleccion_route(coleccion, subcoleccion):
    return get_items_by_subcoleccion(coleccion=coleccion, subcoleccion=subcoleccion)


# ------------------------------
# Devuelve el listado completo de colecciones disponibles.
# Acepta el parámetro de query opcional "sin_subcolecciones" como filtro.
@xmlibris_bp.route("/getallcollections", methods=["GET"])
def get_all_collections_route():
    # Filtro opcional recibido por query string: /getallcollections?sin_subcolecciones=...
    subcolecciones_filtro = request.args.get("sin_subcolecciones")
    return get_all_collections(subcolecciones_filtro=subcolecciones_filtro)


# ------------------------------
# Devuelve una colección específica a partir de su internal_id.
# Recibe el internal_id en la URL.
@xmlibris_bp.route("/getcollection/<internal_id>", methods=["GET"])
def get_collection_by_internal_id_route(internal_id):
    return get_collection_by_internal_id(internal_id=internal_id)


# ------------------------------
# Descarga/entrega un archivo adjunto de un ítem.
# Recibe colección, subcolección, internal_id del ítem y nombre del archivo en la URL.
@xmlibris_bp.route(
    "/getfile/<coleccion>/<subcoleccion>/<internal_id>/<archivo>", methods=["GET"]
)
def get_file_route(coleccion, subcoleccion, internal_id, archivo):
    return get_file(
        coleccion=coleccion,
        subcoleccion=subcoleccion,
        internal_id=internal_id,
        archivo=archivo,
    )


# ------------------------------
# Devuelve los campos (esquema/metadatos) definidos para las colecciones.
@xmlibris_bp.route("/getcampos", methods=["GET"])
def get_campos_route():
    return get_campos_controller()


# ============== Peticiones POST ==============
# Crea una nueva colección.
# Requiere rol de escritura y recibe un JSON que se valida con NuevaColeccionSchema.
@xmlibris_bp.route("/newcollection", methods=["POST"])
@require_roles(*ROLES_ESCRITURA)
@validar_con(NuevaColeccionSchema)
def new_collection_route(validated_data):
    return new_collection_controller(
        new_collection_data=validated_data,
    )


# ------------------------------
# Crea una nueva subcolección dentro de una colección.
# Requiere rol de escritura y recibe un JSON validado con NuevaSubcoleccionSchema.
@xmlibris_bp.route("/newsubcollection", methods=["POST"])
@require_roles(*ROLES_ESCRITURA)
@validar_con(NuevaSubcoleccionSchema)
def new_subcollection_route(validated_data):
    return new_subcollection_controller(
        new_subcollection_data=validated_data,
    )


# ------------------------------
# Crea un nuevo ítem dentro de una subcolección, con sus archivos adjuntos.
# Requiere rol de escritura; los archivos se reciben vía multipart/form-data
# en los campos "files" (múltiples) o "file" (único).
# Acepta .jpg, .jpeg, .png, .pdf y .zip.
# El query param "libro" activa el flujo de libro: un único .zip con los
# archivos en la raíz, numerados, y el nombre define el orden.
def _libro_desde_query(valor_por_defecto=False) -> bool:
    valor = request.args.get("libro")
    if valor is None:
        return valor_por_defecto
    return valor.strip().lower() not in {"0", "false", "no"}


@xmlibris_bp.route("/newitem", methods=["POST"])
@require_roles(*ROLES_ESCRITURA)
@validar_schema()
def new_item_route(validated_data):
    files = request.files.getlist("files")
    if not files:
        files = request.files.getlist("file")

    libro_por_defecto = bool(
        validated_data.get("libro", False) or validated_data.get("zip_upload_id")
    )
    return new_item(
        new_item_data=validated_data,
        files=files,
        libro=_libro_desde_query(libro_por_defecto),
    )


# ------------------------------
# Recibe el ZIP de un libro como CUERPO CRUDO (Content-Type: application/zip,
# no multipart) y lo deja en FILES_ROOT/tmp. Devuelve un upload_id que después
# viaja en el alta del item como "zip_upload_id".
# Pensado para archivos de varios GB: se escribe por bloques, sin bufferizar.
@xmlibris_bp.route("/upload", methods=["POST"])
@require_roles(*ROLES_ESCRITURA)
def upload_zip_route():
    return subir_zip()


# ============== Peticiones PUT ==============
# Actualiza una subcolección existente a partir de su internal_id.
# Requiere rol de escritura y un cuerpo JSON con los campos a modificar.
@xmlibris_bp.route("/<coleccion>/subcoleccion/<internal_id>", methods=["PUT"])
@require_roles(*ROLES_ESCRITURA)
def update_subcoleccion(coleccion, internal_id):
    data = request.get_json()
    if not data:
        return {"success": False, "message": "Datos JSON no proporcionados"}, 400

    return actualizar_subcoleccion(
        coleccion=coleccion, internal_id=internal_id, data=data
    )


# ------------------------------
# Actualiza un ítem existente a partir de su internal_id.
# Requiere rol de escritura y un cuerpo JSON con los campos a modificar.
@xmlibris_bp.route("/<coleccion>/item/<internal_id>", methods=["PUT"])
@require_roles(*ROLES_ESCRITURA)
def update_item(coleccion, internal_id):
    data = request.get_json()
    if not data:
        return {"success": False, "message": "Datos JSON no proporcionados"}, 400

    return actualizar_item(coleccion=coleccion, internal_id=internal_id, data=data)
