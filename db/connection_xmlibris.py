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


LIMITE_RESULTADOS = 100


_cliente = None


def _cliente_mongo():
    global _cliente
    if _cliente is None:
        # Comentar server_api si se usa MongoLocal
        _cliente = MongoClient(uri, server_api=ServerApi("1"))
    return _cliente


class MongoDBConnection_XMLibris:

    def __init__(self, collection_name):
        self.client = _cliente_mongo()
        self.db = self.client["xmlibris"]
        self.collection = self.db[collection_name]

    def test_connection(self):
        try:
            self.client.admin.command("ping")
            logger.info("Conexión a MongoDB exitosa")
            return {
                "status": "ok",
                "message": "Conexión a MongoDB exitosa",
                "database": self.db.name,
                "collection": self.collection.name,
            }
        except Exception as e:
            logger.error(f"Error al conectar a MongoDB: {e}")
            return {
                "status": "error",
                "message": str(e),
                "database": self.db.name,
                "collection": self.collection.name,
            }

    def get_all_campos(self):
        try:
            proyeccion = {"_id": 0}
            campos = list(self.collection.find({}, proyeccion))
            if not campos:
                return {
                    "success": False,
                    "message": "No se encontraron campos",
                    "data": [],
                    "status": 404,
                }
            return {"success": True, "data": campos, "status": 200}

        except Exception as e:
            logger.error(f"Error al obtener campos: {e}")
            return {"success": False, "message": str(e), "status": 500}

    def get_all_collections(self, subcolecciones_filtro):
        try:
            if subcolecciones_filtro:
                proyeccion = {
                    "_id": 0,
                    "exportacion_fija": 0,
                    "schema": 0,
                    "subcolecciones": 0,
                }
            else:
                proyeccion = {"_id": 0, "exportacion_fija": 0, "schema": 0}

            collections = list(self.collection.find({}, proyeccion))
            if not collections:
                return {
                    "success": False,
                    "message": "No se encontraron colecciones",
                    "data": [],
                    "status": 404,
                }
            return {"success": True, "data": collections, "status": 200}
        except Exception as e:
            logger.error(f"Error al obtener colecciones: {e}")
            return {"success": False, "message": str(e), "status": 500}

    def get_collection_by_internal_id(self, internal_id):
        try:

            coleccion = self.collection.find_one({"coleccion.internal_id": internal_id})
            if not coleccion:
                return {
                    "success": False,
                    "message": "Colección no encontrada",
                    "status": 404,
                }
            return {"success": True, "data": coleccion, "status": 200}
        except Exception as e:
            logger.error(f"Error al obtener la colección {internal_id}: {e}")
            return {"success": False, "message": str(e), "status": 500}

    def get_all_subcolecciones(self, nombre_coleccion):
        try:
            coleccion = self.collection.find_one(
                {"coleccion.setspec_collection": nombre_coleccion}
            )
            if not coleccion:
                return {
                    "success": False,
                    "message": "Colección no encontrada",
                    "data": [],
                    "status": 404,
                }
            subcolecciones = coleccion.get("subcolecciones") or []
            data, hay_mas = self._recortar(subcolecciones)
            return {
                "success": True,
                "data": data,
                "pagination": self._paginacion(len(data), hay_mas),
                "status": 200,
            }
        except Exception as e:
            logger.error(f"Error al obtener subcolecciones: {e}")
            return {"success": False, "message": str(e), "status": 500}

    def get_items_by_subcoleccion(self, nombre_coleccion, subcoleccion):
        try:
            data = list(
                self.collection.find(
                    {
                        "parents.coleccion.setspec_collection": nombre_coleccion,
                        "parents.subcoleccion.setspec_subcollection": subcoleccion,
                    }
                ).limit(LIMITE_RESULTADOS + 1)
            )
            data, hay_mas = self._recortar(data)
            return {
                "success": True,
                "data": data,
                "pagination": self._paginacion(len(data), hay_mas),
                "status": 200,
            }
        except Exception as e:
            logger.error(f"Error al obtener items por subcolección: {e}")
            return {"success": False, "message": str(e), "status": 500}

    @staticmethod
    def get_file_location(nombre_coleccion, subcoleccion, internal_id, archivo):
        try:
            raiz = os.getenv("FILES_ROOT")
            if not raiz:
                return {
                    "success": False,
                    "message": "FILES_ROOT no está configurado",
                    "status": 500,
                }
            componentes = [nombre_coleccion, subcoleccion, internal_id, archivo]
            for componente in componentes:
                if (
                    not componente
                    or componente in (".", "..")
                    or os.path.basename(componente) != componente
                ):
                    return {
                        "success": False,
                        "message": "Ruta inválida",
                        "status": 400,
                    }
            raiz_abs = os.path.abspath(raiz)
            destino = os.path.join(raiz_abs, *componentes)
            if not destino.startswith(raiz_abs + os.sep):
                return {"success": False, "message": "Ruta inválida", "status": 400}
            if not os.path.isfile(destino):
                return {
                    "success": False,
                    "message": "Archivo no encontrado",
                    "status": 404,
                }
            return {"success": True, "data": {"ruta": destino}, "status": 200}
        except Exception as e:
            logger.error(f"Error al localizar el archivo: {e}")
            return {"success": False, "message": str(e), "status": 500}

    def update_subcoleccion(self, nombre_coleccion, internal_id, data):
        try:
            updated_doc = self.collection.find_one_and_update(
                {
                    "coleccion.setspec_collection": nombre_coleccion,
                    "subcolecciones.internal_id": internal_id,
                },
                {
                    "$set": {
                        f"subcolecciones.$[sub].{campo}": valor
                        for campo, valor in data.items()
                    }
                },
                array_filters=[{"sub.internal_id": internal_id}],
                return_document=ReturnDocument.AFTER,
            )
            if not updated_doc:
                return {
                    "success": False,
                    "message": "Subcolección no encontrada",
                    "status": 404,
                }
            subcoleccion = next(
                (
                    sub
                    for sub in updated_doc.get("subcolecciones") or []
                    if sub.get("internal_id") == internal_id
                ),
                None,
            )
            return {
                "success": True,
                "message": "Subcolección actualizada exitosamente",
                "data": subcoleccion,
                "status": 200,
            }
        except Exception as e:
            logger.error(f"Error al actualizar subcolección: {e}")
            return {"success": False, "message": str(e), "status": 500}

    def update_item(self, nombre_coleccion, internal_id, data):
        try:
            updated_doc = self.collection.find_one_and_update(
                {
                    "internal_id": internal_id,
                    "parents.coleccion.setspec_collection": nombre_coleccion,
                },
                {"$set": data},
                return_document=ReturnDocument.AFTER,
            )
            if not updated_doc:
                return {
                    "success": False,
                    "message": "Item no encontrado",
                    "status": 404,
                }
            return {
                "success": True,
                "message": "Item actualizado exitosamente",
                "data": updated_doc,
                "status": 200,
            }
        except Exception as e:
            logger.error(f"Error al actualizar item: {e}")
            return {"success": False, "message": str(e), "status": 500}

    @staticmethod
    def _recortar(data):
        """Recorta al tope de resultados e indica si quedaron más."""
        if len(data) > LIMITE_RESULTADOS:
            return data[:LIMITE_RESULTADOS], True
        return data, False

    @staticmethod
    def _paginacion(cantidad, hay_mas):
        return {
            "limit": LIMITE_RESULTADOS,
            "returned": cantidad,
            "has_more": hay_mas,
        }

    def _registro_de_coleccion(self, nombre_coleccion):
        return self.db["colecciones"].find_one(
            {"coleccion.setspec_collection": nombre_coleccion}
        )

    def new_collection(self, data: dict):
        try:
            result = self.collection.insert_one(data)

            if not result.inserted_id:
                return {
                    "success": False,
                    "message": "No se pudo crear la colección",
                    "status": 500,
                }

            try:
                creada = self.collection.find_one({"_id": result.inserted_id})
            except Exception as e:
                logger.error(f"Error al leer la colección recién creada: {e}")
                creada = None
            if not creada:
                creada = {**data, "_id": result.inserted_id}

            return {
                "success": True,
                "message": "Colección creada correctamente",
                "data": creada,
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

    def new_subcollection(self, data: dict, internal_id: str):
        try:
            result = self.collection.find_one_and_update(
                {"coleccion.internal_id": internal_id},
                {"$push": {"subcolecciones": data}},
            )
            if not result:
                return {
                    "success": False,
                    "message": "Coleccion no encontrada",
                    "status": 404,
                }
            return {
                "success": True,
                "message": "Subcolección agregada exitosamente",
                "status": 200,
            }
        except Exception as e:
            logger.error(f"Error al crear subcoleccion: {e}")
            return {"success": False, "message": str(e), "status": 500}

    def new_item(self, data: dict):
        try:
            result = self.collection.insert_one(data)
            if not result.inserted_id:
                return {
                    "success": False,
                    "message": "Error al guardar el item",
                    "status": 500,
                }
            return {
                "success": True,
                "message": "Item agregado exitosamente",
                "status": 200,
            }
        except Exception as e:
            logger.error(f"Error al crear item: {e}")
            return {"success": False, "message": str(e), "status": 500}
