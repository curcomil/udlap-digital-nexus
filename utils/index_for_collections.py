from xml.etree.ElementTree import SubElement, register_namespace
import re

register_namespace("xsi", "http://www.w3.org/2001/XMLSchema-instance")


def add_if_value(parent, tag, value, xsi_type=None):
    if value:
        text = str(value).strip()
        if text:
            elem = SubElement(parent, tag)
            elem.text = text
            if xsi_type:
                elem.set("xsi:type", xsi_type)


def normalize_languages(value):
    if not value:
        return []

    LANG_MAP = {
        "español": "spa",
        "en español": "spa",
        "castellano": "spa",
        "espanol": "spa",
        "latin": "lat",
        "latín": "lat",
        "nahuatl": "nah",
        "náhuatl": "nah",
    }

    partes = [p.strip().lower() for p in re.split(r"<br\s*/?>", value) if p.strip()]

    return list({LANG_MAP.get(p, "und") for p in partes})


def index_4_collections(record, dc, identifier):
    coleccion = record.get("coleccion")
    md = record.get("metadata", {})

    match coleccion:

        case "Archivo Miguel Covarrubias":

            add_if_value(dc, "dc:title", md.get("titulo"))
            add_if_value(dc, "dc:creator", md.get("autor"))
            add_if_value(dc, "dc:description", md.get("descripcion"))
            add_if_value(dc, "dc:format", md.get("tecnica"))
            add_if_value(dc, "dcterms:extent", md.get("medidas"))
            add_if_value(dc, "dcterms:identifier", md.get("numero"))

            add_if_value(
                dc, "dc:isPartOf", record.get("subcoleccion"), "dcterms:isPartOf"
            )

            add_if_value(dc, "dc:relation", coleccion, "dcterms:isPartOf")
            add_if_value(dc, "dc:source", record.get("item_url"))
            add_if_value(dc, "dc:source", record.get("portada_url"), "dcterms:URI")

            SubElement(dc, "dc:identifier").text = identifier
            SubElement(dc, "dc:type").text = "images"

        case "Archivo Histórico de la Provincia del Santo Evangelio de México":

            add_if_value(dc, "dc:title", md.get("titulo"))

            autor = md.get("autor")
            SubElement(dc, "dc:creator").text = (
                autor.strip() if autor and autor.strip() else "Sin autor"
            )

            add_if_value(
                dc,
                "dc:description",
                md.get("descripcion_fisica_y_notas") or md.get("descripcion_fisica"),
            )
            add_if_value(
                dc, "dcterms:spatial", md.get("lugar") or md.get("lugar_de_impresion")
            )
            add_if_value(
                dc, "dc:date", md.get("fecha") or md.get("fecha_de_publicacion")
            )

            for lang in normalize_languages(md.get("idioma")):
                SubElement(dc, "dc:language").text = lang

            add_if_value(dc, "dcterms:provenance", md.get("procedencia"))
            add_if_value(dc, "dc:contributor", md.get("impresor"))

            add_if_value(dc, "dc:relation", coleccion, "dcterms:isPartOf")
            add_if_value(dc, "dc:source", record.get("item_url"))
            add_if_value(dc, "dc:source", record.get("portada_url"), "dcterms:URI")
            add_if_value(dc, "dcterms:hasPart", md.get("marcas_de_propiedad"))

            SubElement(dc, "dc:identifier").text = identifier
            SubElement(dc, "dc:type").text = "archival_material_manuscript"

        case _:
            add_if_value(dc, "dc:title", md.get("titulo"))
            SubElement(dc, "dc:identifier").text = identifier
