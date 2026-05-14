from flask import jsonify
from db import MongoDBConnection_Auth


def register(db: str, coleccion: str, data: dict):
    mongo = MongoDBConnection_Auth(db_name=db, collection_name=coleccion)
    result = mongo.register_user(data)
    status = result.pop("status", 500)
    return jsonify(result), status


def login(db: str, coleccion: str, data: dict):
    mongo = MongoDBConnection_Auth(db_name=db, collection_name=coleccion)
    result = mongo.login_user(data)
    status = result.pop("status", 500)
    return jsonify(result), status
