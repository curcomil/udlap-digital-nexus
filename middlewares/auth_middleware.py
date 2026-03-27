from flask_jwt_extended import jwt_required, get_jwt
from flask import jsonify
from functools import wraps


def require_admin(f):
    @wraps(f)
    @jwt_required()  # verifica firma y expiración automáticamente
    def decorated(*args, **kwargs):
        claims = get_jwt()  # obtiene el payload completo
        if claims.get("role") != "admin":
            return jsonify({"success": False, "message": "Acceso restringido"}), 403
        return f(*args, **kwargs)

    return decorated


def require_coordinator(f):
    @wraps(f)
    @jwt_required()  # verifica firma y expiración automáticamente
    def decorated(*args, **kwargs):
        claims = get_jwt()  # obtiene el payload completo
        if claims.get("role") != "coordinator":
            return jsonify({"success": False, "message": "Acceso restringido"}), 403
        return f(*args, **kwargs)

    return decorated


def require_digitalizer(f):
    @wraps(f)
    @jwt_required()  # verifica firma y expiración automáticamente
    def decorated(*args, **kwargs):
        claims = get_jwt()  # obtiene el payload completo
        if claims.get("role") != "digitizer":
            return jsonify({"success": False, "message": "Acceso restringido"}), 403
        return f(*args, **kwargs)

    return decorated
