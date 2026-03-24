from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv
from bson import ObjectId
from pymongo.errors import WriteError
import os

load_dotenv()
uri = os.getenv("MONGODB_URI")


class MongoDBConnection_Users:
    def __init__(self, db_name: str, collection_name: str):
        # Comentar server_api si se usa MongoLocal
        self.client = MongoClient(uri, server_api=ServerApi("1"))
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]

    def get__users(self):
        result = list(self.collection.find({}))
        return result

    def update_user(self, data: dict, id: str):
        try:
            user_up = self.collection.find_one_and_update(
                {"_id": ObjectId(id)}, {"$set": data}
            )
            if not user_up:
                return {
                    "success": False,
                    "message": "Usuario no encontrado",
                    "status": 404,
                }

            return {
                "success": True,
                "message": "Usuario actualizado correctamente",
                "status": 200,
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"Error al actualizar usuario: {e}",
                "status": 500,
            }

    def create_user(self, data: dict):
        try:
            result = self.collection.insert_one(data)

            if not result.inserted_id:
                return {
                    "success": False,
                    "message": "No se pudo crear el usuario",
                    "status": 500,
                }

            return {
                "success": True,
                "message": "Usuario creado correctamente",
                "status": 201,
            }

        except WriteError as e:

            missing = []
            try:
                rules = e.details["errInfo"]["details"]["schemaRulesNotSatisfied"]
                for rule in rules:
                    if rule.get("operatorName") == "required":
                        missing = rule.get("missingProperties", [])
            except (KeyError, TypeError):
                pass

            message = "Faltan campos requeridos"
            if missing:
                message = f"Faltan campos requeridos: {', '.join(missing)}"

            return {
                "success": False,
                "message": message,
                "status": 400,
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"Error al crear usuario: {e}",
                "status": 500,
            }

    def delete_user(self, id: str):
        try:
            user_for_delete = self.collection.find_one_and_delete({"_id": ObjectId(id)})
            if not user_for_delete:
                return {
                    "success": False,
                    "message": "Usuario no encontrado",
                    "status": 404,
                }

            return {
                "success": True,
                "message": "Usuario eliminado correctamente",
                "status": 200,
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"Error al actualizar usuario: {e}",
                "status": 500,
            }

    def reset_credentials(self, id: str):
        try:
            result = self.collection.find_one_and_update(
                {"_id": ObjectId(id)},
                {"$set": {"username": None, "password": None}},
            )

            if not result:
                return {
                    "success": False,
                    "message": "Usuario no encontrado",
                    "status": 404,
                }

            return {
                "success": True,
                "message": "Credenciales reiniciadas correctamente",
                "status": 200,
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"Error al reiniciar credenciales: {e}",
                "status": 500,
            }
