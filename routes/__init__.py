from .oai_routes import oai_bp
from .xmlibris_routes import xmlibris_bp
from .auth_routes import auth_bp
from .users_routes import users_bp
from .mets_routes import mets_bp


blueprints = [
    (oai_bp, "/oai"),
    (xmlibris_bp, "/xmlibris"),
    (auth_bp, "/auth"),
    (users_bp, "/users"),
    (mets_bp, "/mets"),
]
