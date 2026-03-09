from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from pymongo import ReturnDocument
from dotenv import load_dotenv
import os
from flask import current_app as app


load_dotenv()
uri = os.getenv("MONGODB_URI")


class MongoDBConnection_XMLibris:

    def __init__(self, collection_name):
        # Comentar server_api si se usa MongoLocal
        self.client = MongoClient(uri, server_api=ServerApi("1"))
        self.db = self.client["xmlibris"]
        self.collection = self.db[collection_name]

    def get_all_carpetas(self):
        try:
            return list(self.collection.find({"type": "carpeta"}))
        except Exception as e:
            app.logger.error(f"Error al obtener datos: {e}")
            return []

    def get_carpeta_by_id(self, carpeta_id):
        try:
            return self.collection.find_one({"_id": carpeta_id, "type": "carpeta"})
        except Exception as e:
            app.logger.error(f"Error al obtener carpeta por ID: {e}")
            return None

    def get_all_items(self):
        try:
            return list(self.collection.find({"type": "item"}))
        except Exception as e:
            app.logger.error(f"Error al obtener datos: {e}")
            return []

    def get_items_by_carpeta_id(self, carpeta_id):
        try:
            return list(self.collection.find({"type": "item", "father_id": carpeta_id}))
        except Exception as e:
            app.logger.error(f"Error al obtener datos: {e}")
            return []

    def update_carpeta(self, carpeta_id, data):
        try:
            updated_doc = self.collection.find_one_and_update(
                {"_id": carpeta_id, "type": "carpeta"},
                {"$set": data},
                return_document=ReturnDocument.AFTER,
            )
            return updated_doc
        except Exception as e:
            app.logger.error(f"Error al actualizar carpeta: {e}")
            return None

    def update_item(self, item_id, data):
        try:
            updated_doc = self.collection.find_one_and_update(
                {"_id": item_id, "type": "item"},
                {"$set": data},
                return_document=ReturnDocument.AFTER,
            )
            return updated_doc
        except Exception as e:
            app.logger.error(f"Error al actualizar item: {e}")
            return None

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

            return result

        except Exception as e:
            app.logger.error(f"Error en la busqueda: {e}")
            return None