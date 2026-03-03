from .oai_routes import oai_bp
from .xmlibris_routes import xmlibris_bp
from flask_cors import CORS

blueprints = [
    (oai_bp, "/oai"),
    (xmlibris_bp, "/xmlibris"),
]

CORS(xmlibris_bp, origins=["http://localhost:3000"])
