import json
from functools import wraps

from flask import jsonify, request
from pydantic import ValidationError


def _respuesta_error(mensaje, status, detalles=None):
    cuerpo = {"success": False, "message": mensaje}
    if detalles is not None:
        cuerpo["detalles"] = detalles
    return jsonify(cuerpo), status


def validar_con(modelo_pydantic):

    def decorador(f):
        @wraps(f)
        def func_envuelta(*args, **kwargs):
            if not request.is_json:
                return _respuesta_error(
                    "El Content-Type debe ser application/json", 400
                )

            try:
                datos_validados = modelo_pydantic.model_validate(request.get_json())

            except ValidationError as e:
                return _respuesta_error(
                    "Los datos enviados no son válidos",
                    422,
                    json.loads(e.json()),
                )

            kwargs["validated_data"] = datos_validados.model_dump(by_alias=True)
            return f(*args, **kwargs)

        return func_envuelta

    return decorador
