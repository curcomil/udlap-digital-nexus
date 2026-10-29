from flask import Flask, request, jsonify
from routes import blueprints
from dotenv import load_dotenv
from db import MongoDBConnection_XMLibris
from utils import get_debug_docs
from flask_jwt_extended import JWTManager
from middlewares import jwt_handlers_messages
from datetime import timedelta
from werkzeug.exceptions import HTTPException
import os
import logging

load_dotenv()
app = Flask(__name__)
ENVIROMENT = os.getenv("ENVIROMENT") or "production"
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=8)

# El navegador no puede leer la cookie httpOnly del token, así que además del
# header (que usan las server actions de Next) se acepta el token desde cookie.
# Eso habilita las peticiones directas del navegador al mismo origen, necesarias
# para subir un ZIP de varios GB sin pasar por Next.
# La cookie ya viaja con SameSite=Lax, que impide el envío en POST cross-site;
# por eso se desactiva la protección CSRF de flask-jwt-extended.
app.config["JWT_TOKEN_LOCATION"] = ["headers", "cookies"]
app.config["JWT_ACCESS_COOKIE_NAME"] = "token"
app.config["JWT_COOKIE_CSRF_PROTECT"] = False
jwt = JWTManager(app)
jwt_handlers_messages(jwt)


logging.basicConfig(level=logging.INFO)


@app.errorhandler(HTTPException)
def _respuesta_http(error):
    """Cualquier error HTTP sale en JSON, no en el HTML por defecto de Flask.

    Cubre 404 de ruta inexistente, 405 de método incorrecto, 415 cuando falta el
    Content-Type y los 400 de parseo del body.
    """
    return jsonify({"success": False, "message": error.description}), error.code


@app.errorhandler(Exception)
def _respuesta_error(error):
    """Errores no controlados: se registran y se devuelve JSON 500.

    En debug el traceback sigue saliendo en consola vía logger.exception; si
    prefieres el depurador interactivo de Flask, comenta este handler.
    """
    logging.getLogger(__name__).exception("Error no controlado")
    return jsonify({"success": False, "message": "Error interno del servidor"}), 500

"""
@app.before_request
def log_request_info():
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    app.logger.info(f">>> IP CLIENTE: {ip} | RUTA: {request.path} | MÉTODO: {request.method}")
"""


@app.route("/api", strict_slashes=False)
def home():
    if ENVIROMENT == "debug":
        db_status = MongoDBConnection_XMLibris("items").test_connection()
        return get_debug_docs("api", db_connection=db_status)
    return {"message": "UDLAP API."}


API_PREFIX = "/api"

for bp, prefix in blueprints:

    app.register_blueprint(bp, url_prefix=API_PREFIX + prefix)

if __name__ == "__main__" and ENVIROMENT == "debug":

    """
    @app.before_request
    def log_headers():
        print("=== HEADERS RECIBIDOS ===")
        print(f"Metodo: {request.method}")
        print(f"URL: {request.url}")
        print(f"Path: {request.path}")
        for header, value in request.headers:
            print(f"{header}: {value}")
        print("========================")
    """
    app.run(host="127.0.0.1", port=5000, debug=True)
