from xml.etree.ElementTree import Element, SubElement, tostring
from datetime import datetime
from .index_for_collections import index_4_collections

def render_get_record_xml(record, base_url, identifier, metadata_prefix="oai_dc", set_spec="und"):
    """
    Genera el XML para un item
    """
    root = create_oai_root()
    
    SubElement(root, "responseDate").text = datetime.utcnow().strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )

    request = SubElement(
        root,
        "request",
        {
            "verb": "GetRecord",
            "identifier": identifier,
            "metadataPrefix": metadata_prefix,
        },
    )
    request.text = base_url

    get_record = SubElement(root, "GetRecord")
    record_el = SubElement(get_record, "record")

    # Crear el header y metadata usando funciones auxiliares
    create_record_header(record_el, identifier, record, set_spec)
    create_record_metadata(record_el, record, identifier, metadata_prefix)

    if "titulo" not in record["metadata"]:
        return None
    
    return tostring(root, encoding="utf-8", xml_declaration=True)

# ============================================

def render_list_records_xml(records, base_url, metadata_prefix, set_filter=None, date_from=None, date_until=None):
    """
    Genera el XML para ListRecords reutilizando las funciones auxiliares
    """
    root = create_oai_root()
    
    SubElement(root, "responseDate").text = datetime.utcnow().strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )

    request_attrs = {
        "verb": "ListRecords",
        "metadataPrefix": metadata_prefix,
    }
    if set_filter:
        request_attrs["set"] = set_filter
    if date_from:
        request_attrs["from"] = date_from
    if date_until:
        request_attrs["until"] = date_until

    request = SubElement(root, "request", request_attrs)
    request.text = base_url

    list_records_el = SubElement(root, "ListRecords")

    # Iterar sobre cada registro y crear su elemento
    for record_data in records:
        record_el = SubElement(list_records_el, "record")
        
        create_record_header(
            record_el, 
            record_data["identifier"], 
            record_data["record"], 
            record_data["setSpec"]
        )
        create_record_metadata(
            record_el, 
            record_data["record"], 
            record_data["identifier"], 
            metadata_prefix
        )

    return tostring(root, encoding="utf-8", xml_declaration=True)


# ============================================
# Funciones auxiliares compartidas
# ============================================

def create_oai_root():
    """Crea el elemento raíz OAI-PMH"""
    return Element(
        "OAI-PMH",
        {
            "xmlns": "http://www.openarchives.org/OAI/2.0/",
            "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
            "xsi:schemaLocation": (
                "http://www.openarchives.org/OAI/2.0/ "
                "http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd"
            ),
        },
    )


def create_record_header(record_el, identifier, record, set_spec):
    """Crea el elemento header de un registro"""
    def parse_oai_date(date_str: str) -> str | None:
        try:
            return date_str.split(" ")[0]
        except Exception:
            return None

    header = SubElement(record_el, "header")
    SubElement(header, "identifier").text = identifier
    SubElement(header, "datestamp").text = parse_oai_date(
        record["metadata"].get("mdate", datetime.utcnow().strftime("%Y-%m-%d"))
    )
    SubElement(header, "setSpec").text = set_spec

    # Si el registro tiene setSpec adicionales
    for additional_set_spec in record.get("setSpec", []):
        SubElement(header, "setSpec").text = additional_set_spec


def create_record_metadata(record_el, record, identifier, metadata_prefix):
    """Crea el elemento metadata de un registro"""
    
    metadata = SubElement(record_el, "metadata")

    if metadata_prefix == "oai_dc":
        dc = SubElement(
            metadata,
            "oai_dc:dc",
            {
                "xmlns:oai_dc": "http://www.openarchives.org/OAI/2.0/oai_dc/",
                "xmlns:dc": "http://purl.org/dc/elements/1.1/",
                "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
                "xmlns:dcterms": "http://purl.org/dc/terms/",
                "xsi:schemaLocation": (
                    "http://www.openarchives.org/OAI/2.0/oai_dc/ "
                    "http://www.openarchives.org/OAI/2.0/oai_dc.xsd"
                ),
            },
        )

        #AQUI VA EL INDEX DE COLECCIONES

        index_4_collections(record, dc, identifier)
