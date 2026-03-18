from flask import jsonify


def jwt_handlers_messages(jwt):  # Mensajes de retorno la validación del token

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({"success": False, "message": "Token expirado"}), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({"success": False, "message": "Token inválido"}), 401

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({"success": False, "message": "Token requerido"}), 401
