import os
from flask_cors import CORS
from flask import Blueprint, request
from controllers import register, login

auth_bp = Blueprint("auth", __name__)
CORS(auth_bp, origins="*")


@auth_bp.route("/", methods=["GET"])
def auth_root():
    if os.getenv("ENVIROMENT") == "debug":
        return {
            "message": "Auth root endpoint.",
            "available_endpoints": [
                {"path": "/xmlibris/register", "method": "POST"},
                {"path": "/xmlibris/login", "method": "POST"},
            ],
        }
    return {"message": "Auth endpoint."}


@auth_bp.route("/xmlibris/register", methods=["POST"])
def register_():
    data = request.get_json()
    if not data:
        return {"success": False, "message": "Datos JSON no proporcionados"}, 400
    return register(db="xmlibris", coleccion="users", data=data)


@auth_bp.route("/xmlibris/login", methods=["POST"])
def login_():
    data = request.get_json()
    if not data:
        return {"success": False, "message": "Datos JSON no proporcionados"}, 400
    return login(db="xmlibris", coleccion="users", data=data)
