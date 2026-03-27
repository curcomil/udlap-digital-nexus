from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash
from flask_jwt_extended import create_access_token
import os

load_dotenv()
uri = os.getenv("MONGODB_URI")


class MongoDBConnection_Auth:

    def __init__(self, db_name: str, collection_name: str):
        # Comentar server_api si se usa MongoLocal
        self.client = MongoClient(uri, server_api=ServerApi("1"))
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]

    def register_user(self, data: dict):

        password = data.get("password")
        username = data.get("username")
        email = data.get("email")

        if not password or not username or not email:
            return {
                "success": False,
                "message": "Faltan datos requeridos",
                "status": 400,
            }

        auth_user = self.collection.find_one({"email": email})

        if not auth_user:
            return {
                "success": False,
                "message": "Tu correo no se encuentra autorizado, contacta al administrador",
                "status": 403,
            }

        if auth_user.get("username"):
            return {
                "success": False,
                "message": "Este usuario ya fue registrado",
                "status": 409,
            }

        existing_user = self.collection.find_one({"username": username})

        if existing_user:
            return {"success": False, "message": "El usuario ya existe", "status": 409}

        password_hash = generate_password_hash(password)

        result = self.collection.update_one(
            {"email": email},
            {"$set": {"username": username, "password": password_hash}},
        )

        if result.modified_count == 0:
            return {
                "success": False,
                "message": "No se pudo completar el registro",
                "status": 500,
            }

        return {
            "success": True,
            "message": "Usuario registrado correctamente",
            "status": 201,
        }

    def login_user(self, data: dict):
        username = data.get("username")
        password = data.get("password")

        if not username or not password:
            return {"success": False, "message": "Faltan credenciales", "status": 400}

        user = self.collection.find_one(
            {"$or": [{"username": username}, {"email": username}]}
        )

        if not user:
            return {"success": False, "message": "Usuario no encontrado", "status": 404}

        if not user.get("password"):
            return {"success": False, "message": "Usuario no registrado", "status": 403}

        if not user.get("isActive", True):
            return {"success": False, "message": "Usuario desactivado", "status": 403}

        if not check_password_hash(user["password"], password):
            return {"success": False, "message": "Contraseña incorrecta", "status": 401}

        token = create_access_token(
            identity=str(user["_id"]),
            additional_claims={"username": user["username"], "role": user["role"]},
        )

        return {
            "success": True,
            "message": "Login exitoso",
            "token": token,
            "user": {
                "username": user["username"],
                "name": user["name"],
                "role": user["role"],
                "_id": user["_id"],
            },
            "status": 200,
        }
