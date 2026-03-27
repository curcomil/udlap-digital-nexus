from flask import jsonify
from db import MongoDBConnection_Users


def getUsers(db: str, coleccion: str):

    mongo = MongoDBConnection_Users(db_name=db, collection_name=coleccion)
    result = mongo.get__users()

    if not result:
        return (
            jsonify(
                {"success": False, "message": "No se encontraron usuarios", "data": []}
            ),
            404,
        )

    for user in result:
        user["_id"] = str(user["_id"])
        if user.get("password"):
            user["password"] = True
        else:
            user["password"] = False

    return (
        jsonify({"success": True, "message": "Consulta exitosa", "data": result}),
        200,
    )


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

    if not result:
        return (
            jsonify(
                {"success": False, "message": "No se encontraron usuarios", "data": []}
            ),
            404,
        )

    coordinators = []
    for user in result:
        user["_id"] = str(user["_id"])

        keys_to_remove = {
            "isActive",
            "accessibleRoles",
            "assignedCollections",
            "role",
            "password",
        }

        user_dict = {k: v for k, v in user.items() if k not in keys_to_remove}
        coordinators.append(user_dict)

    return (
        jsonify({"success": True, "message": "Consulta exitosa", "data": coordinators}),
        200,
    )
