from flask import jsonify
from db import MongoDBConnection_Users


def getUsers(db: str, coleccion: str):
    mongo = MongoDBConnection_Users(db_name=db, collection_name=coleccion)
    result = mongo.get__users()
    status = result.pop("status", 500)

    if result.get("success") and result.get("data"):
        for user in result["data"]:
            user["_id"] = str(user["_id"])
            user["password"] = bool(user.get("password"))

    return jsonify(result), status


def updateUser(id_user: str, new_data: dict, db: str, coleccion: str):
    mongo = MongoDBConnection_Users(db_name=db, collection_name=coleccion)
    result = mongo.update_user(id=id_user, data=new_data)
    status = result.pop("status", 500)
    return jsonify(result), status


def new_user(new_data: dict, db: str, coleccion: str):
    mongo = MongoDBConnection_Users(db_name=db, collection_name=coleccion)
    result = mongo.create_user(data=new_data)
    status = result.pop("status", 500)
    return jsonify(result), status


def delete_user_controller(id_user: str, db: str, coleccion: str):
    mongo = MongoDBConnection_Users(db_name=db, collection_name=coleccion)
    result = mongo.delete_user(id=id_user)
    status = result.pop("status", 500)
    return jsonify(result), status


def reset_credentials_controller(id_user: str, db: str, coleccion: str):
    mongo = MongoDBConnection_Users(db_name=db, collection_name=coleccion)
    result = mongo.reset_credentials(id=id_user)
    status = result.pop("status", 500)
    return jsonify(result), status


def get_coordinators_controller(db: str, coleccion: str):
    mongo = MongoDBConnection_Users(db_name=db, collection_name=coleccion)
    result = mongo.get_coordinators()
    status = result.pop("status", 500)

    if result.get("success") and result.get("data"):
        keys_to_remove = {"isActive", "accessibleRoles", "assignedCollections", "role", "password"}
        coordinators = []
        for user in result["data"]:
            user["_id"] = str(user["_id"])
            coordinators.append({k: v for k, v in user.items() if k not in keys_to_remove})
        result["data"] = coordinators

    return jsonify(result), status
