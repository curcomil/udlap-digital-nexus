from flask_cors import CORS
from flask import Blueprint, request
from middlewares import require_admin
from controllers import getUsers

users_bp = Blueprint("users", __name__)
CORS(users_bp, origins="*")


@users_bp.route("/", methods=["GET"])
def users_root():
    return {
        "message": "users root enpoint",
        "avalible_endpoints": ["/getusers"],
    }


@users_bp.route("/getusers", methods=["GET"])
@require_admin
def get_users():
    return getUsers(db="xmlibris", coleccion="users")
