from flask import Flask
from routes import blueprints
from dotenv import load_dotenv
import os

load_dotenv()
app = Flask(__name__)

@app.route("/api")
def home ():
    app.logger.info(f"Acceso a home")
    return {"mensaje": "q pedo api"}

for bp, prefix in blueprints:
    app.register_blueprint(bp, url_prefix=prefix)

