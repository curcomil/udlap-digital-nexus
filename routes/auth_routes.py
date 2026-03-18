from flask_cors import CORS
from flask import Blueprint, request
from controllers import register, login

auth_bp = Blueprint("auth", __name__)
CORS(auth_bp, origins="*")


@auth_bp.route("/", methods=["GET"])
def auth_root():
    return {
        "message": "auth root enpoint",
        "avalible_endpoints": ["/xmlibris", "/tesis"],
    }


@auth_bp.route("/xmlibris/register", methods=["POST"])
def register_():
    data = request.get_json()
    return register(db="xmlibris", coleccion="users", data=data)


@auth_bp.route("/xmlibris/login", methods=["POST"])
def login_():
    data = request.get_json()
    return login(db="xmlibris", coleccion="users", data=data)
