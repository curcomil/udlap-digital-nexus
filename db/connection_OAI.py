from http import client
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv
import os
from flask import current_app as app

load_dotenv()
uri = os.getenv("MONGODB_URI")


class MongoDBConnection_OAI:

    def __init__(self, collection_name):
        self.client = MongoClient(
            uri, server_api=ServerApi("1")
        )  # Comentar server_api si se usa MongoLocal
        self.db = self.client["OAI"]
        self.collection = self.db[collection_name]

    def test_connection(self):
        try:
            self.client.admin.command('ping')
            app.logger.info("Conexión a MongoDB exitosa")
            return {"message": "Conexión a MongoDB exitosa"}
        except Exception as e:
            app.logger.error(f"Error al conectar a MongoDB: {e}")
            return {"error": "No se pudo conectar a MongoDB", "details": str(e)}, 500


    def get_all(self):
        try:
            return list(self.collection.find())
        except Exception as e:
            app.logger.error(f"Error al obtener datos: {e}")
            return []

    def set_filter(self, coleccion, subcoleccion):
        try:
            query = {"coleccion.setspec_collection": coleccion}
            
            if subcoleccion:
                query["subcolecciones.setspec_subcollection"] = subcoleccion

            return self.collection.find_one(query)

        except Exception as e:
            app.logger.error(f"Error al obtener datos: {e}")
            return None

    def find_items(self, coleccion, subcoleccion):
        try:
            query = {"coleccion": coleccion}
            if subcoleccion:
                query["subcoleccion"] = subcoleccion

            
            return list(self.collection.find(query, {"_id": 0}))

        except Exception as e:
            app.logger.error(f"Error al obtener datos: {e}")
            return []  