import os
from flask_cors import CORS
from flask import Blueprint, request
from middlewares import require_admin, require_digitalizer
from controllers import (
    getUsers,
    updateUser,
    new_user,
    delete_user_controller,
    reset_credentials_controller,
    get_coordinators_controller,
)
from bson import ObjectId

users_bp = Blueprint("users", __name__)
CORS(users_bp, origins="*")


@users_bp.route("/", methods=["GET"])
def users_root():
    if os.getenv("ENVIROMENT") == "debug":
        return {
            "message": "Users root endpoint.",
            "note": "Todos los endpoints requieren JWT. Admin: la mayoría. Digitalizer: /getcoordinators.",
            "available_endpoints": [
                {"path": "/getusers", "method": "GET", "auth": "admin"},
                {"path": "/create", "method": "POST", "auth": "admin"},
                {"path": "/<user_id>", "method": "PATCH", "auth": "admin"},
                {"path": "/<user_id>", "method": "DELETE", "auth": "admin"},
                {"path": "/reset_credentials/<user_id>", "method": "DELETE", "auth": "admin"},
                {"path": "/getcoordinators", "method": "GET", "auth": "digitalizer"},
            ],
        }
    return {"message": "Users endpoint."}


@users_bp.route("/getusers", methods=["GET"])
@require_admin
def get_users():
    return getUsers(db="xmlibris", coleccion="users")


@users_bp.route("/<user_id>", methods=["PATCH"])
@require_admin
def update_user(user_id):
    if not ObjectId.is_valid(user_id):
        return {"success": False, "message": "ID inválido"}, 400

    data = request.get_json()
    if not data:
        return {"success": False, "message": "Datos JSON no proporcionados"}, 400

    return updateUser(id_user=user_id, new_data=data, db="xmlibris", coleccion="users")


@users_bp.route("/create", methods=["POST"])
@require_admin
def NEW_user():

    data = request.get_json()
    if not data:
        return {"success": False, "message": "Datos JSON no proporcionados"}, 400

    return new_user(new_data=data, db="xmlibris", coleccion="users")


@users_bp.route("/<user_id>", methods=["DELETE"])
@require_admin
def delete_user_route(user_id):
    if not ObjectId.is_valid(user_id):
        return {"success": False, "message": "ID inválido"}, 400

    return delete_user_controller(id_user=user_id, coleccion="users", db="xmlibris")


@users_bp.route("/reset_credentials/<user_id>", methods=["DELETE"])
@require_admin
def reset_credentials_route(user_id):
    if not ObjectId.is_valid(user_id):
        return {"success": False, "message": "ID inválido"}, 400

    return reset_credentials_controller(
        id_user=user_id, coleccion="users", db="xmlibris"
    )


@users_bp.route("/getcoordinators", methods=["GET"])
@require_digitalizer
def get_coordinators_route():
    return get_coordinators_controller(db="xmlibris", coleccion="users")
