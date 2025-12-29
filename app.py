from flask import Flask
from routes import blueprints
from dotenv import load_dotenv
import os

load_dotenv()
app = Flask(__name__)

@app.route("/api", strict_slashes=False)
def home ():
    app.logger.info(f"Acceso a home")
    return {"mensaje": "q pedo api"}

API_PREFIX = "/api"

for bp, prefix in blueprints:
    app.register_blueprint(bp, url_prefix=API_PREFIX + prefix)

