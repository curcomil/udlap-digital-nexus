from pathlib import Path
from flask import Response
from datetime import datetime
import os
from utils import (
    jsonToOAI,
    build_list_identifiers,
    render_get_record_xml,
    render_list_records_xml,
)
import json
from flask import current_app as app
import xml.etree.ElementTree as ET
import re
import unicodedata

URL = os.getenv("URL") or "unknown"
DEPLOY_BASE_PATH = Path(__file__).resolve().parent.parent
ROOT_PATH = DEPLOY_BASE_PATH / "db" / "json"
RECORDS_PATH = DEPLOY_BASE_PATH / "db" / "json" / "records"


def oai_error(code: str, message: str) -> Response:

    # Retorna un error OAI-PMH válido

    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/
                             http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd">
  <responseDate>{datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")}</responseDate>
  <error code="{code}">{message}</error>
</OAI-PMH>"""

    return Response(xml, status=200, mimetype="text/xml; charset=utf-8")


def identify(repositorio):
    """Responde al verbo Identify del protocolo OAI-PMH."""
    repoIdentifier = (
        "coleccionesdigitales"
        if repositorio == "colecciones_digitales"
        else "tesisdigitales"
    )

    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/
                             http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd">
  <responseDate>{datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')}</responseDate>
  <request verb="Identify">{URL}/oai</request>
  <Identify>
    <repositoryName>Colecciones Digitales - UDLAP</repositoryName>
    <baseURL>{URL}/oai/{repositorio}</baseURL>
    <protocolVersion>2.0</protocolVersion>
    <adminEmail>tesis.digitales@udlap.mx</adminEmail>
    <earliestDatestamp>2000-01-01T00:00:00Z</earliestDatestamp>
    <deletedRecord>no</deletedRecord>
    <granularity>YYYY-MM-DDThh:mm:ssZ</granularity>
    <description>
      <oai-identifier xmlns="http://www.openarchives.org/OAI/2.0/oai-identifier"
                      xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                      xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/oai-identifier
                                          http://www.openarchives.org/OAI/2.0/oai-identifier.xsd">
        <scheme>oai</scheme>
        <repositoryIdentifier>{repoIdentifier}.udlap.mx</repositoryIdentifier>
        <delimiter>:</delimiter>
        <sampleIdentifier>oai:{repoIdentifier}.udlap.mx:17612469923493441</sampleIdentifier>
      </oai-identifier>
    </description>
  </Identify>
</OAI-PMH>"""

    return Response(xml, content_type="text/xml; charset=utf-8")


def list_metadata_formats():
    """Responde al verbo ListMetadataFormats."""
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/
                             http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd">
  <responseDate>{datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')}</responseDate>
  <request verb="ListMetadataFormats">{URL}/oai</request>
  <ListMetadataFormats>
    <metadataFormat>
      <metadataPrefix>oai_dc</metadataPrefix>
      <schema>http://www.openarchives.org/OAI/2.0/oai_dc.xsd</schema>
      <metadataNamespace>http://www.openarchives.org/OAI/2.0/oai_dc/</metadataNamespace>
    </metadataFormat>
    <metadataFormat>
      <metadataPrefix>oai_etdms</metadataPrefix>
      <schema>http://www.ndltd.org/standards/metadata/etdms/1.0/etdms.xsd</schema>
      <metadataNamespace>http://www.ndltd.org/standards/metadata/etdms/1.0/</metadataNamespace>
    </metadataFormat>
  </ListMetadataFormats>
</OAI-PMH>"""
    return Response(xml, content_type="text/xml; charset=utf-8")


def list_sets():

    try:
        if not ROOT_PATH:
            app.logger.error("json_database_path no está definido")
            return oai_error(
                "internalServerError", "Error interno, contacte al administrador"
            )

        json_path = os.path.join(ROOT_PATH, "estructura_sets.json")

        if not os.path.isfile(json_path):
            app.logger.error("estructura_sets.json no encontrado")
            return oai_error(
                "internalServerError", "Error interno, contacte al administrador"
            )

        xml_str = jsonToOAI(json_path, URL)

        return Response(xml_str, status=200, mimetype="text/xml; charset=utf-8")

    except json.JSONDecodeError as e:
        app.logger.error(f"JSON mal formado: {e}")
        return oai_error(
            "internalServerError", "Error interno, contacte al administrador"
        )

    except Exception as e:
        app.logger.exception("Error inesperado en ListSets")
        return oai_error(
            "internalServerError", "Error interno, contacte al administrador"
        )


def list_identifiers(
    metadata_prefix=None,
    set_filter=None,
    date_from=None,
    date_until=None,
    repositorio=None,
):

    # Responde al verbo ListIdentifiers
    repoIdentifier = (
        "coleccionesdigitales"
        if repositorio == "colecciones_digitales"
        else "tesisdigitales"
    )

    def render_list_identifiers_xml(headers: list[dict]) -> str:
        NS = "http://www.openarchives.org/OAI/2.0/"
        XSI = "http://www.w3.org/2001/XMLSchema-instance"
        SCHEMA = (
            "http://www.openarchives.org/OAI/2.0/ "
            "http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd"
        )

        ET.register_namespace("", NS)
        ET.register_namespace("xsi", XSI)

        root = ET.Element(f"{{{NS}}}OAI-PMH", {f"{{{XSI}}}schemaLocation": SCHEMA})

        # responseDate
        response_date = ET.SubElement(root, "responseDate")
        response_date.text = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

        # request
        request = ET.SubElement(root, "request", {"verb": "ListIdentifiers"})
        request.text = ""

        # ListIdentifiers
        list_identifiers = ET.SubElement(root, "ListIdentifiers")

        for h in headers:
            header = ET.SubElement(list_identifiers, "header")

            identifier = ET.SubElement(header, "identifier")
            identifier.text = h["identifier"]

            datestamp = ET.SubElement(header, "datestamp")
            datestamp.text = h["datestamp"]

            set_spec = ET.SubElement(header, "setSpec")
            set_spec.text = h["setSpec"]

        return ET.tostring(root, encoding="utf-8", xml_declaration=True).decode("utf-8")

    try:
        headers = build_list_identifiers(
            data_path=RECORDS_PATH,
            base_url=repoIdentifier + ".udlap.mx",
            metadata_prefix=metadata_prefix,
            set_filter=set_filter,
            date_from=date_from,
            date_until=date_until,
        )

        if not headers:
            return oai_error("noRecordsMatch", "No hay registros")

        return render_list_identifiers_xml(headers)

    except ValueError as e:
        if str(e) == "cannotDisseminateFormat":
            return oai_error("cannotDisseminateFormat", "Formato no soportado")

        return oai_error("badArgument", "Argumentos inválidos")


def get_record(identifier, metadata_prefix="oai_dc", repositorio=None):

    if not repositorio or not identifier.startswith(repositorio):
        return oai_error("badArgument", "Invalid identifier")

    internal_id = identifier[len(repositorio) :]

    def find_id(id_for_find):

        def normalizar_setspec(texto: str) -> str:
            texto = texto.lower()
            texto = unicodedata.normalize("NFKD", texto)
            texto = texto.encode("ascii", "ignore").decode("ascii")
            texto = re.sub(r"[^a-z0-9]+", "_", texto)
            return texto.strip("_")

        try:
            record_data = {
                "record": {},
                "setSpec": "",
            }
            for file in os.listdir(RECORDS_PATH):
                if not file.endswith(".json"):
                    continue

                with open(os.path.join(RECORDS_PATH, file), "r", encoding="utf-8") as f:
                    collection_data = json.load(f)

                subcolecciones = collection_data.get("subcolecciones", [])
                for subcoleccion in subcolecciones:
                    items = subcoleccion.get("items", [])

                    for idx, item in enumerate(items):
                        if not isinstance(item, dict):
                            app.logger.warning(
                                f"Item inválido en archivo={file}, "
                                f"subcolección={subcoleccion.get('name')}, "
                                f"index={idx}, "
                                f"type={type(item)}, "
                                f"value={item}"
                            )
                            continue

                        if item.get("internal_id") == id_for_find:
                            collection_name = normalizar_setspec(
                                collection_data.get("coleccion", file)
                            )
                            sub_name = normalizar_setspec(subcoleccion.get("name"))
                            record_data["setSpec"] = f"{collection_name}:{sub_name}"
                            record_data["record"] = item
                            return record_data
        except Exception as e:
            app.logger.exception("Error buscando el ID", e)
            return None

    record = find_id(internal_id)

    if not record:
        return oai_error("idDoesNotExist", "Record not found")

    xml = render_get_record_xml(
        record=record["record"],
        base_url=f"{URL}/api/oai/colecciones_digitales",
        identifier=identifier,
        metadata_prefix=metadata_prefix,
        set_spec=record["setSpec"],
    )

    return Response(xml, content_type="text/xml; charset=utf-8", status=200)


def list_records(
    metadata_prefix=None,
    set_filter=None,
    date_from=None,
    date_until=None,
    repositorio=None,
):
    def normalizar_setspec(texto: str) -> str:
        texto = texto.lower()
        texto = unicodedata.normalize("NFKD", texto)
        texto = texto.encode("ascii", "ignore").decode("ascii")
        texto = re.sub(r"[^a-z0-9]+", "_", texto)
        return texto.strip("_")

    def parse_oai_date(date_str: str) -> str | None:
        try:
            return date_str.split(" ")[0]
        except Exception:
            return None

    if not metadata_prefix:
        return oai_error("badArgument", "Missing metadataPrefix")

    repoIdentifier = (
        "coleccionesdigitales"
        if repositorio == "colecciones_digitales"
        else "tesisdigitales"
    )

    # Lista para almacenar los registros que coinciden
    matching_records = []

    try:
        for file in os.listdir(RECORDS_PATH):
            if not file.endswith(".json"):
                continue

            with open(os.path.join(RECORDS_PATH, file), "r", encoding="utf-8") as f:
                collection_data = json.load(f)

            # Comparar con set_filter
            collection_name = normalizar_setspec(collection_data.get("coleccion", file))

            if set_filter:
                for sub in collection_data.get("subcolecciones", []):
                    sub_name = normalizar_setspec(sub.get("name"))
                    set_spec = f"{collection_name}:{sub_name}"

                    if set_spec != set_filter:
                        continue

                    # Filtro de fecha
                    for item in sub.get("items", []):
                        if not isinstance(item, dict):
                            app.logger.warning(
                                f"Item inválido en archivo={file}, "
                                f"subcolección={sub.get('name')}, "
                                f"type={type(item)}, "
                                f"value={item}"
                            )
                            continue
                        internal_id = item.get("internal_id")
                        mdate_raw = item.get("metadata", {}).get("mdate")

                        if not internal_id or not mdate_raw:
                            continue

                        datestamp = parse_oai_date(mdate_raw)
                        if not datestamp:
                            continue

                        if date_from and datestamp < date_from:
                            continue
                        if date_until and datestamp > date_until:
                            continue

                        # Agregar el registro a la lista
                        matching_records.append(
                            {
                                "record": item,
                                "setSpec": set_spec,
                                "identifier": f"oai:{repoIdentifier}.udlap.mx:{internal_id}",
                            }
                        )
                # Si no hay registros, retornar error
                if not matching_records:
                    return oai_error("noRecordsMatch", "No records found")
            else:
                # Sin filtro de set, revisar todas las subcolecciones
                for sub in collection_data.get("subcolecciones", []):
                    sub_name = normalizar_setspec(sub.get("name"))
                    set_spec = f"{collection_name}:{sub_name}"

                    for item in sub.get("items", []):
                        if not isinstance(item, dict):
                            app.logger.warning(
                                f"Item inválido en archivo={file}, "
                                f"subcolección={sub.get('name')}, "
                                f"type={type(item)}, "
                                f"value={item}"
                            )
                            continue
                        internal_id = item.get("internal_id")
                        mdate_raw = item.get("metadata", {}).get("mdate")

                        if not internal_id or not mdate_raw:
                            continue

                        datestamp = parse_oai_date(mdate_raw)
                        if not datestamp:
                            continue

                        if date_from and datestamp < date_from:
                            continue
                        if date_until and datestamp > date_until:
                            continue

                        # Agregar el registro a la lista
                        matching_records.append(
                            {
                                "record": item,
                                "setSpec": set_spec,
                                "identifier": f"oai:{repoIdentifier}.udlap.mx:{internal_id}",
                            }
                        )
        # Generar el XML usando la función reutilizada
        xml = render_list_records_xml(
            records=matching_records,
            base_url=f"{URL}/api/oai/{repositorio}",
            metadata_prefix=metadata_prefix,
            set_filter=set_filter,
            date_from=date_from,
            date_until=date_until,
        )

        return Response(xml, content_type="text/xml; charset=utf-8", status=200)

    except ValueError as e:
        app.logger.exception("Error en list_records", e)
        return oai_error("badArgument", "Invalid arguments")
