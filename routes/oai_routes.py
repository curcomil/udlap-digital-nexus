from flask import Blueprint, request
from controllers import identify, list_metadata_formats, list_sets

oai_bp = Blueprint("oai", __name__)

@oai_bp.route("/", methods=["GET"])
def oai_root():
    return {
        "message": "OAI root endpoint.",
        "available_endpoints": ["/colecciones_digitales", "/tesis_digitales"]
    }

@oai_bp.route("/colecciones_digitales", methods =["GET"])
def oai_colecciones():
    verb = request.args.get("verb")

    if not verb:
        return {"error": "Missing required parameter verb"}, 400
    
    if verb == "Identify":
        return identify()
    
    elif verb == "ListMetadataFormats":
        return list_metadata_formats()
    
    elif verb == "ListSets":
        return list_sets()
    
    return {"error": f"Unsupported verb: {verb}"}, 400