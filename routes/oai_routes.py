from flask import current_app as app
from flask import Blueprint, request
from controllers import (
    identify,
    list_metadata_formats,
    list_sets,
    list_identifiers,
    get_record,
    list_records,
)

oai_bp = Blueprint("oai", __name__)


@oai_bp.route("/", methods=["GET"])
def oai_root():
    return {
        "message": "OAI root endpoint.",
        "available_endpoints": ["/colecciones_digitales", "/tesis_digitales"],
    }


@oai_bp.route("/colecciones_digitales", methods=["GET"])
def oai_colecciones():

    metadata_prefix = request.args.get("metadataPrefix") or "oai_dc"
    set_filter = request.args.get("set")
    date_from = request.args.get("from")
    date_until = request.args.get("until")
    identifier = request.args.get("identifier")

    verb = request.args.get("verb")

    if not verb:
        return {"error": "Missing required parameter verb"}, 400

    if verb == "Identify":
        return identify("colecciones_digitales")

    elif verb == "ListMetadataFormats":
        return list_metadata_formats()

    elif verb == "ListSets":
        return list_sets()

    elif verb == "ListIdentifiers": 

        return list_identifiers(
            metadata_prefix=metadata_prefix,
            set_filter=set_filter,
            date_from=date_from,
            date_until=date_until,
            repositorio="colecciones_digitales",
        )

    elif verb == "GetRecord": #Este es el que sigue
        app.logger.info(
            f"GetRecord called with identifier={identifier}, metadataPrefix={metadata_prefix}"
        )
        return get_record(
            identifier,
            metadata_prefix,
            repositorio="oai:coleccionesdigitales.udlap.mx:",
        )

    elif verb == "ListRecords":
        app.logger.info(
            f"ListRecords called with metadataPrefix={metadata_prefix}, set={set_filter}, from={date_from}, until={date_until}"
        )
        return list_records(
            metadata_prefix=metadata_prefix,
            set_filter=set_filter,
            date_from=date_from,
            date_until=date_until,
            repositorio="colecciones_digitales",
        )

    return {"error": f"Unsupported verb: {verb}"}, 400
