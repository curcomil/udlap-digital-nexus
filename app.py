from flask import Flask, request
from routes import blueprints
from dotenv import load_dotenv
import os

load_dotenv()
app = Flask(__name__)
ENVIROMENT = os.getenv("ENVIROMENT") or "production"


@app.route("/api", strict_slashes=False)
def home():
    app.logger.info(f"Acceso a home")
    return {"mensaje": "q pedo api"}


API_PREFIX = "/api"

for bp, prefix in blueprints:
    app.register_blueprint(bp, url_prefix=API_PREFIX + prefix)

if __name__ == "__main__" and ENVIROMENT == "debug":
    
    @app.before_request
    def log_headers():
        print("=== HEADERS RECIBIDOS ===")
        print(f"Metodo: {request.method}")
        print(f"URL: {request.url}")
        print(f"Path: {request.path}")
        for header, value in request.headers:
            print(f"{header}: {value}")
        print("========================")
    
    app.run(host="127.0.0.1", port=5000, debug=True)
