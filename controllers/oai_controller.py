from flask import Response
from datetime import datetime
import logging
import os
from utils import (
    jsonToOAI,
    build_list_identifiers,
    render_get_record_xml,
    render_list_records_xml,
    normalizar,
    setfilter,
    parse_oai_date,
)
import xml.etree.ElementTree as ET
from db import MongoDBConnection_OAI

URL = os.getenv("URL") or "unknown"
logger = logging.getLogger(__name__)


def oai_error(code: str, message: str) -> Response:
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
        repo_estructura = MongoDBConnection_OAI("estructura")
        data = repo_estructura.get_all()
        xml_str = jsonToOAI(data, URL)
        return Response(xml_str, status=200, mimetype="text/xml; charset=utf-8")
    except Exception as e:
        logger.exception("Error inesperado en ListSets")
        return oai_error("internalServerError", "Error interno, contacte al administrador")


def list_identifiers(
    metadata_prefix=None,
    set_filter=None,
    date_from=None,
    date_until=None,
    repositorio=None,
):
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

        response_date = ET.SubElement(root, "responseDate")
        response_date.text = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

        request = ET.SubElement(
            root, "request", {"verb": "ListIdentifiers", "metadataPrefix": "oai_dc"}
        )
        request.text = URL + f"/api/oai/{repositorio}"

        list_identifiers_el = ET.SubElement(root, "ListIdentifiers")

        for h in headers:
            header = ET.SubElement(list_identifiers_el, "header")
            ET.SubElement(header, "identifier").text = h["identifier"]
            ET.SubElement(header, "datestamp").text = h["datestamp"]
            ET.SubElement(header, "setSpec").text = h["setSpec"]

        return ET.tostring(root, encoding="utf-8", xml_declaration=True).decode("utf-8")

    try:
        repo_items = MongoDBConnection_OAI("items")

        if set_filter:
            prefijo, _, sufijo = set_filter.partition(":")
            repo_estructura = MongoDBConnection_OAI("estructura")
            estructura_data = repo_estructura.set_filter(prefijo, sufijo if sufijo else None)
            filtros = setfilter(set_filter, estructura_data)
            col_id = filtros[0] if filtros else None
            sub_id = filtros[1] if len(filtros) > 1 else None
            items = repo_items.find_items(col_id, sub_id)
        else:
            items = repo_items.get_all()

        headers = build_list_identifiers(
            base_url=repoIdentifier + ".udlap.mx",
            metadata_prefix=metadata_prefix,
            items=items,
            date_from=date_from,
            date_until=date_until,
        )

        if not headers:
            return oai_error("noRecordsMatch", "No hay registros")

        xml = render_list_identifiers_xml(headers)
        return Response(xml, content_type="text/xml; charset=utf-8", status=200)

    except ValueError as e:
        if str(e) == "cannotDisseminateFormat":
            return oai_error("cannotDisseminateFormat", "Formato no soportado")
        return oai_error("badArgument", "Argumentos inválidos")


def get_record(identifier, metadata_prefix="oai_dc", repositorio=None):

    if not repositorio or not identifier.startswith(repositorio):
        return oai_error("badArgument", "Invalid identifier")

    internal_id = identifier[len(repositorio):]
    repo_items = MongoDBConnection_OAI("items")

    try:
        item = repo_items.find_item(internal_id)
    except Exception as e:
        logger.exception("Error buscando el ID")
        return oai_error("idDoesNotExist", "Record not found")

    if not item:
        return oai_error("idDoesNotExist", "Record not found")

    set_spec = (
        f"{normalizar(item.get('coleccion', 'unknown'))}:"
        f"{normalizar(item.get('subcoleccion', 'unknown'))}"
    )

    xml = render_get_record_xml(
        record=item,
        base_url=f"{URL}/api/oai/colecciones_digitales",
        identifier=identifier,
        metadata_prefix=metadata_prefix,
        set_spec=set_spec,
    )

    if xml is None:
        return oai_error("cannotDisseminateFormat", "Record metadata is incomplete")

    return Response(xml, content_type="text/xml; charset=utf-8", status=200)


def list_records(
    metadata_prefix=None,
    set_filter=None,
    date_from=None,
    date_until=None,
    repositorio=None,
):
    if not metadata_prefix:
        return oai_error("badArgument", "Missing metadataPrefix")

    repoIdentifier = (
        "coleccionesdigitales"
        if repositorio == "colecciones_digitales"
        else "tesisdigitales"
    )

    try:
        repo_items = MongoDBConnection_OAI("items")

        if set_filter:
            prefijo, _, sufijo = set_filter.partition(":")
            repo_estructura = MongoDBConnection_OAI("estructura")
            estructura_data = repo_estructura.set_filter(prefijo, sufijo if sufijo else None)
            filtros = setfilter(set_filter, estructura_data)
            col_id = filtros[0] if filtros else None
            sub_id = filtros[1] if len(filtros) > 1 else None
            items = repo_items.find_items(col_id, sub_id)
        else:
            items = repo_items.get_all()

        final_records = []
        for item in items:
            mdate_raw = item.get("metadata", {}).get("mdate")
            datestamp = parse_oai_date(mdate_raw) if mdate_raw else None

            if not datestamp:
                continue
            if date_from and datestamp < date_from:
                continue
            if date_until and datestamp > date_until:
                continue

            col_norm = normalizar(item.get("coleccion", ""))
            sub_raw = item.get("subcoleccion")
            sub_norm = normalizar(sub_raw) if sub_raw else None

            final_records.append(
                {
                    "record": item,
                    "setSpec": f"{col_norm}:{sub_norm}" if sub_norm else col_norm,
                    "identifier": f"oai:{repoIdentifier}.udlap.mx:{item.get('internal_id')}",
                }
            )

        xml = render_list_records_xml(
            records=final_records,
            base_url=f"{URL}/api/oai/{repositorio}",
            metadata_prefix=metadata_prefix,
            set_filter=set_filter,
            date_from=date_from,
            date_until=date_until,
        )

        return Response(xml, content_type="text/xml; charset=utf-8", status=200)

    except Exception as e:
        logger.exception(f"Error en list_records: {e}")
        return oai_error("badArgument", "Invalid arguments or database error")
