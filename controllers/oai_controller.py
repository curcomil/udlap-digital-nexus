from flask import Response
from datetime import datetime
import os
from utils import generate_json, jsonToOAI
import json

url = os.getenv("URL") or "unknown"
root_path = os.getenv("exist_database_path")


def identify():
    """Responde al verbo Identify del protocolo OAI-PMH."""
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/
                             http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd">
  <responseDate>{datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')}</responseDate>
  <request verb="Identify">{url}/oai</request>
  <Identify>
    <repositoryName>Colecciones Digitales - UDLAP</repositoryName>
    <baseURL>{url}/oai</baseURL>
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
        <repositoryIdentifier>udlap.mx</repositoryIdentifier>
        <delimiter>:</delimiter>
        <sampleIdentifier>oai:udlap.mx:covarrubias/africa-001</sampleIdentifier>
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
  <request verb="ListMetadataFormats">{url}/oai</request>
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
        json_path = os.path.join(root_path, "estructura_exist.json")

        if not os.path.exists(json_path):
            print("Archivo JSON no encontrado, generando nuevo...")
            estructura = generate_json()
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(estructura, f, indent=4, ensure_ascii=False)
        else:
            with open(json_path, "r", encoding="utf-8") as f:
                estructura = json.load(f)

        xml_str = jsonToOAI(estructura, url)

        return Response(xml_str, mimetype="text/xml; charset=utf-8")

    except FileNotFoundError:
        print("Error: No se encontró el archivo JSON ni la base de datos EXIST.")
        return Response(
            "<error>JSON no encontrado</error>", status=500, mimetype="text/xml"
        )

    except json.JSONDecodeError as e:
        print(f"Error al decodificar el JSON: {e}")
        return Response("<error>JSON inválido</error>", status=500, mimetype="text/xml")

    except Exception as e:
        print(f"Error inesperado: {e}")
        return Response(f"<error>{e}</error>", status=500, mimetype="text/xml")
