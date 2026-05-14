from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from pymongo import ReturnDocument
from pymongo.errors import WriteError
from dotenv import load_dotenv
import logging
import os

load_dotenv()
uri = os.getenv("MONGODB_URI")
logger = logging.getLogger(__name__)


class MongoDBConnection_XMLibris:

    def __init__(self, collection_name):
        # Comentar server_api si se usa MongoLocal
        self.client = MongoClient(uri, server_api=ServerApi("1"))
        self.db = self.client["xmlibris"]
        self.collection = self.db[collection_name]

    def get_all_carpetas(self):
        try:
            data = list(self.collection.find({"type": "carpeta"}))
            if not data:
                return {"success": False, "message": "No se encontraron carpetas", "data": [], "status": 404}
            return {"success": True, "data": data, "status": 200}
        except Exception as e:
            logger.error(f"Error al obtener carpetas: {e}")
            return {"success": False, "message": str(e), "status": 500}

    def get_carpeta_by_id(self, carpeta_id):
        try:
            carpeta = self.collection.find_one({"_id": carpeta_id, "type": "carpeta"})
            if not carpeta:
                return {"success": False, "message": "Carpeta no encontrada", "status": 404}
            return {"success": True, "data": carpeta, "status": 200}
        except Exception as e:
            logger.error(f"Error al obtener carpeta por ID: {e}")
            return {"success": False, "message": str(e), "status": 500}

    def get_all_items(self):
        try:
            data = list(self.collection.find({"type": "item"}))
            if not data:
                return {"success": False, "message": "No se encontraron items", "data": [], "status": 404}
            return {"success": True, "data": data, "status": 200}
        except Exception as e:
            logger.error(f"Error al obtener items: {e}")
            return {"success": False, "message": str(e), "status": 500}

    def get_items_by_carpeta_id(self, carpeta_id):
        try:
            data = list(self.collection.find({"type": "item", "father_id": carpeta_id}))
            if not data:
                return {"success": False, "message": "No se encontraron items para esta carpeta", "data": [], "status": 404}
            return {"success": True, "data": data, "status": 200}
        except Exception as e:
            logger.error(f"Error al obtener items por carpeta: {e}")
            return {"success": False, "message": str(e), "status": 500}

    def update_carpeta(self, carpeta_id, data):
        try:
            updated_doc = self.collection.find_one_and_update(
                {"_id": carpeta_id, "type": "carpeta"},
                {"$set": data},
                return_document=ReturnDocument.AFTER,
            )
            if not updated_doc:
                return {"success": False, "message": "Carpeta no encontrada o sin cambios", "status": 404}
            return {"success": True, "message": "Carpeta actualizada exitosamente", "data": updated_doc, "status": 200}
        except Exception as e:
            logger.error(f"Error al actualizar carpeta: {e}")
            return {"success": False, "message": str(e), "status": 500}

    def update_item(self, item_id, data):
        try:
            updated_doc = self.collection.find_one_and_update(
                {"_id": item_id, "type": "item"},
                {"$set": data},
                return_document=ReturnDocument.AFTER,
            )
            if not updated_doc:
                return {"success": False, "message": "Item no encontrado o sin cambios", "status": 404}
            return {"success": True, "message": "Item actualizado exitosamente", "data": updated_doc, "status": 200}
        except Exception as e:
            logger.error(f"Error al actualizar item: {e}")
            return {"success": False, "message": str(e), "status": 500}

    def search_by_filters(self, data):
        try:
            type_ = data.get("type")
            filtro = data.get("filtro")
            query_value = data.get("query")

            if filtro == "keywords":
                match_query = {
                    "type": type_,
                    "keywords": {
                        "$elemMatch": {"$regex": query_value, "$options": "i"}
                    },
                }
            else:
                match_query = {
                    "type": type_,
                    filtro: {"$regex": query_value, "$options": "i"},
                }

            pipeline = [
                {"$match": match_query},
                {
                    "$lookup": {
                        "from": self.collection.name,
                        "localField": "father_id",
                        "foreignField": "_id",
                        "as": "carpeta_padre",
                    }
                },
                {
                    "$unwind": {
                        "path": "$carpeta_padre",
                        "preserveNullAndEmptyArrays": True,
                    }
                },
            ]

            result = list(self.collection.aggregate(pipeline))

            for item in result:
                if not item.get("carpeta_padre"):
                    item["carpeta_padre"] = "Sin carpeta asignada"

            if not result:
                return {"success": False, "message": "Sin coincidencias", "data": [], "status": 404}
            return {"success": True, "message": "Búsqueda exitosa", "data": result, "status": 200}

        except Exception as e:
            logger.error(f"Error en la búsqueda: {e}")
            return {"success": False, "message": str(e), "status": 500}

    def new_collection(self, data: dict):
        try:
            result = self.collection.insert_one(data)

            if not result.inserted_id:
                return {
                    "success": False,
                    "message": "No se pudo crear la colección",
                    "status": 500,
                }

            return {
                "success": True,
                "message": "Colección creada correctamente",
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
                "message": f"Error al crear la colección: {e}",
                "status": 500,
            }
