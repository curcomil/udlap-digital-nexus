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
