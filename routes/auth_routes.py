import os
from flask_cors import CORS
from flask import Blueprint, request
from controllers import register, login
from utils import get_debug_docs

auth_bp = Blueprint("auth", __name__)
CORS(auth_bp, origins="*")


@auth_bp.route("/", methods=["GET"])
def auth_root():
    if os.getenv("ENVIROMENT") == "debug":
        return get_debug_docs("auth")
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
