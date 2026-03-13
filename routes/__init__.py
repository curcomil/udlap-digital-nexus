from .oai_routes import oai_bp
from .xmlibris_routes import xmlibris_bp
from .auth_routes import auth_bp


blueprints = [(oai_bp, "/oai"), (xmlibris_bp, "/xmlibris"), (auth_bp, "/auth")]
