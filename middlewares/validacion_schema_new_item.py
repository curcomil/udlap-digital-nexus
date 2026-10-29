import json
from functools import wraps
from typing import Any, Dict, List, Literal, Optional

from flask import jsonify, request
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    create_model,
)

from db import MongoDBConnection_XMLibris
from .clases_validacion import ParentSchema


_CAMPOS_RESERVADOS = frozenset(
    {"model_config", "model_fields", "model_computed_fields"}
)


def _respuesta_error(mensaje, status, detalles=None):
    cuerpo = {"success": False, "message": mensaje}
    if detalles is not None:
        cuerpo["detalles"] = detalles
    return jsonify(cuerpo), status


def _a_bool(valor, por_defecto=False):
    if isinstance(valor, bool):
        return valor
    if isinstance(valor, str):
        return valor.strip().lower() in {"1", "true", "si", "sí", "yes"}
    return bool(valor) if valor is not None else por_defecto


def _nombre_campo(item, indice):
    if not isinstance(item, dict):
        raise ValueError(f"El elemento #{indice} del schema no es un objeto")

    nombre = item.get("campo")
    if not isinstance(nombre, str) or not nombre.strip():
        raise ValueError(f"El elemento #{indice} del schema no tiene 'campo'")

    nombre = nombre.strip()
    if nombre.startswith("_") or nombre in _CAMPOS_RESERVADOS:
        raise ValueError(f"El campo '{nombre}' del schema usa un nombre reservado")
    if not nombre.isidentifier():
        raise ValueError(f"El campo '{nombre}' del schema no es un identificador válido")
    return nombre


def construir_modelo_dinamico(schema_coleccion: list):
    campos_dinamicos = {}

    for indice, item in enumerate(schema_coleccion or []):
        nombre_campo = _nombre_campo(item, indice)
        if nombre_campo in campos_dinamicos:
            raise ValueError(f"El campo '{nombre_campo}' está duplicado en el schema")

        es_multiple = _a_bool(item.get("es_multiple"))
        requerido = _a_bool(item.get("requerido"))

        if es_multiple:
            if requerido:
                campos_dinamicos[nombre_campo] = (
                    List[str],
                    Field(..., min_length=1),
                )
            else:
                campos_dinamicos[nombre_campo] = (Optional[List[str]], None)
        elif requerido:
            campos_dinamicos[nombre_campo] = (str, ...)
        else:
            campos_dinamicos[nombre_campo] = (Optional[str], None)

    DatosDinamicosSchema = create_model(
        "DatosDinamicosSchema",
        __config__=ConfigDict(extra="forbid"),
        **campos_dinamicos,
    )

    class NuevoItemDinamico(BaseModel):
        model_config = ConfigDict(extra="forbid", populate_by_name=True)

        parents: ParentSchema
        notas: Optional[str] = None
        origen: Literal["acervo", "tesis"]
        libro: bool = False
        estructura: Dict[str, Any] = Field(default_factory=dict)
        # Identificador del ZIP previamente subido por /upload. El alta lo
        # consume para extraer los archivos sin volver a subirlos.
        zip_upload_id: Optional[str] = None
        # Se acepta tanto "metadata" como el alias "data"; el dump usa
        # "metadata", que es la clave que consume el controller.
        metadata: DatosDinamicosSchema = Field(..., alias="data")

    return NuevoItemDinamico


def _leer_body():
    """Devuelve (body, None) o (None, respuesta_de_error)."""
    if request.is_json:
        body = request.get_json(silent=True)
        if body is None:
            return None, _respuesta_error(
                "El body debe ser un objeto JSON válido", 400
            )
        return body, None

    if request.mimetype == "multipart/form-data":
        data = request.form.get("data")
        if not data:
            return None, _respuesta_error(
                "Falta el campo 'data' con el JSON del item", 400
            )
        try:
            body = json.loads(data)
        except (TypeError, json.JSONDecodeError):
            return None, _respuesta_error(
                "El campo 'data' no contiene un JSON válido", 400
            )
        return body, None

    return None, _respuesta_error(
        "El Content-Type debe ser application/json o multipart/form-data", 400
    )


def _parents_canonicos(registro, parents):
    """Reemplaza los datos de parents con la identidad real de la base."""
    coleccion_doc = registro.get("coleccion")
    if not isinstance(coleccion_doc, dict) or not coleccion_doc.get("internal_id"):
        return None, _respuesta_error(
            "El registro de la colección está incompleto", 500
        )

    subcoleccion_ref = parents.get("subcoleccion") or {}
    subcoleccion_id = subcoleccion_ref.get("internal_id")
    subcolecciones = registro.get("subcolecciones") or []
    subcoleccion_doc = next(
        (
            sub
            for sub in subcolecciones
            if isinstance(sub, dict) and sub.get("internal_id") == subcoleccion_id
        ),
        None,
    )
    if not subcoleccion_doc:
        return None, _respuesta_error(
            "Subcolección no encontrada en la colección indicada", 400
        )

    return {
        "coleccion": {
            "name_collection": coleccion_doc.get("name_collection"),
            "setspec_collection": coleccion_doc.get("setspec_collection"),
            "internal_id": coleccion_doc.get("internal_id"),
        },
        "subcoleccion": {
            "name_subcollection": subcoleccion_doc.get("name_subcollection"),
            "setspec_subcollection": subcoleccion_doc.get("setspec_subcollection"),
            "internal_id": subcoleccion_doc.get("internal_id"),
        },
    }, None


def _validar_multiplicidad(body, schema_coleccion):
    """Valida que cada campo respete el es_multiple de su schema."""
    metadata = body.get("metadata")
    clave_metadata = "metadata"
    if metadata is None:
        metadata = body.get("data")
        clave_metadata = "data"
    if not isinstance(metadata, dict):
        return None

    for item in schema_coleccion:
        campo = item.get("campo")
        if campo not in metadata:
            continue

        valor = metadata[campo]
        if valor is None:
            continue

        es_multiple = _a_bool(item.get("es_multiple"))
        if es_multiple and not isinstance(valor, list):
            return _respuesta_error(
                "Los datos enviados no son válidos",
                422,
                [
                    {
                        "loc": [clave_metadata, campo],
                        "msg": (
                            f"El campo '{campo}' es múltiple; "
                            "debe enviarse como lista"
                        ),
                        "type": "valor_unico_para_campo_multiple",
                    }
                ],
            )

        if not es_multiple and isinstance(valor, list):
            return _respuesta_error(
                "Los datos enviados no son válidos",
                422,
                [
                    {
                        "loc": [clave_metadata, campo],
                        "msg": (
                            f"El campo '{campo}' no es múltiple; "
                            "debe enviarse como valor único, no como lista"
                        ),
                        "type": "lista_para_campo_no_multiple",
                    }
                ],
            )

    return None


def validar_schema():

    def decorador(f):
        @wraps(f)
        def func_envuelta(*args, **kwargs):
            body, error = _leer_body()
            if error:
                return error

            if not isinstance(body, dict):
                return _respuesta_error("El body debe ser un objeto JSON", 400)

            parents = body.get("parents")
            if not isinstance(parents, dict):
                return _respuesta_error("'parents' debe ser un objeto", 400)

            coleccion_ref = parents.get("coleccion")
            if not isinstance(coleccion_ref, dict):
                return _respuesta_error(
                    "'parents.coleccion' debe ser un objeto", 400
                )

            coleccion_id = coleccion_ref.get("internal_id")
            if not isinstance(coleccion_id, str) or not coleccion_id.strip():
                return _respuesta_error(
                    "Internal_id de la colección padre necesario", 400
                )

            coleccion = MongoDBConnection_XMLibris(
                "colecciones"
            ).get_collection_by_internal_id(coleccion_id.strip())
            if not coleccion.get("success"):
                return _respuesta_error(
                    coleccion.get("message", "Colección no encontrada"),
                    coleccion.get("status", 500),
                )

            registro = coleccion.get("data") or {}
            schema_coleccion = registro.get("schema")
            if schema_coleccion is None:
                schema_coleccion = []
            if not isinstance(schema_coleccion, list):
                return _respuesta_error(
                    "El schema de la colección no es válido", 500
                )

            try:
                modelo = construir_modelo_dinamico(schema_coleccion)
            except (TypeError, ValueError) as e:
                return _respuesta_error(
                    f"El schema de la colección no es válido: {e}", 500
                )

            error = _validar_multiplicidad(body, schema_coleccion)
            if error:
                return error

            try:
                datos_validados = modelo.model_validate(body)
            except ValidationError as e:
                return _respuesta_error(
                    "Los datos enviados no son válidos",
                    422,
                    json.loads(e.json()),
                )

            datos = datos_validados.model_dump(by_alias=False)
            parents_canonicos, error = _parents_canonicos(
                registro, datos.get("parents") or {}
            )
            if error:
                return error

            datos["parents"] = parents_canonicos
            kwargs["validated_data"] = datos
            return f(*args, **kwargs)

        return func_envuelta

    return decorador
