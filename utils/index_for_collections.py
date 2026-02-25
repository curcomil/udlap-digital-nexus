from xml.etree.ElementTree import SubElement, register_namespace
import re

# Registrar el prefijo xsi para que ElementTree no lo redeclare en cada elemento hijo
register_namespace("xsi", "http://www.w3.org/2001/XMLSchema-instance")


def normalize_languages(value):
    LANG_MAP_ESP = [
        "español",
        "en español",
        "castellano",
        "espanol",
        "en espanol",
    ]

    LANG_MAP_LATIN = [
        "latín",
        "latin",
        "en latín",
        "en latin",
    ]

    LANG_MAP_NAHUATL = [
        "náhuatl",
        "nahuatl",
        "en náhuatl",
        "en nahuatl",
    ]

    if not value:
        return []

    # dividir por <br>, <br/> o <br />
    idiomas = [i.strip().lower() for i in re.split(r"<br\s*/?>", value)]

    resultado = []

    for idioma in idiomas:
        if idioma in LANG_MAP_ESP:
            resultado.append("spa")
        elif idioma in LANG_MAP_LATIN:
            resultado.append("lat")
        elif idioma in LANG_MAP_NAHUATL:
            resultado.append("nah")
        else:
            resultado.append("und")  # undefined

    return list(set(resultado))


def index_4_collections(record: dict, dc: object, identifier: str):
    coleccion_nombre = record.get("coleccion")
    metadata_interna = record.get("metadata", {})

    match coleccion_nombre:
        case "Archivo Miguel Covarrubias":
            # --- Miguel Covarrubias ---
            if "titulo" in metadata_interna:
                SubElement(dc, "dc:title").text = metadata_interna["titulo"]
            if "autor" in metadata_interna:
                SubElement(dc, "dc:creator").text = metadata_interna["autor"]
            if "descripcion" in metadata_interna:
                SubElement(dc, "dc:description").text = metadata_interna["descripcion"]

            if "tecnica" in metadata_interna:
                SubElement(dc, "dc:format").text = metadata_interna["tecnica"]

            if "medidas" in metadata_interna:
                SubElement(dc, "dcterms:extent").text = metadata_interna["medidas"]

            if "numero" in metadata_interna:
                elem = SubElement(dc, "dcterms:identifier")
                elem.text = metadata_interna["numero"]

            if record.get("subcoleccion"):
                elem = SubElement(dc, "dc:isPartOf")
                elem.text = record["subcoleccion"]
                elem.set("xsi:type", "dcterms:isPartOf")

            # Lo que siempre va -------------------------

            if record.get("coleccion"):
                elem = SubElement(dc, "dc:relation")
                elem.text = record["coleccion"]
                elem.set("xsi:type", "dcterms:isPartOf")

            if record.get("item_url"):
                elem = SubElement(dc, "dc:source")
                elem.text = record["item_url"]

            if record.get("portada_url"):
                elem = SubElement(dc, "dc:source")
                elem.text = record["portada_url"]
                elem.set("xsi:type", "dcterms:URI")

            SubElement(dc, "dc:identifier").text = identifier
            SubElement(dc, "dc:type").text = "images"

        # case 'Nombre de la Nueva Coleccion':
        #

        case "Archivo Histórico de la Provincia del Santo Evangelio de México":
            # --- Archivo Histórico de la Provincia del Santo Evangelio de México ---
            if "titulo" in metadata_interna:
                SubElement(dc, "dc:title").text = metadata_interna["titulo"]

            if "autor" in metadata_interna:
                SubElement(dc, "dc:creator").text = metadata_interna["autor"]
            else:
                SubElement(dc, "dc:creator").text = "Sin autor"

            if "descripcion_fisica_y_notas" in metadata_interna:
                SubElement(dc, "dc:description").text = metadata_interna[
                    "descripcion_fisica_y_notas"
                ]

            if "lugar" in metadata_interna:
                SubElement(dc, "dcterms:spatial").text = metadata_interna["lugar"]

            if "fecha" in metadata_interna:
                SubElement(dc, "dc:date").text = metadata_interna["fecha"]

            if "idioma" in metadata_interna:
                idiomas_normalizados = normalize_languages(metadata_interna["idioma"])
                for idioma in idiomas_normalizados:
                    SubElement(dc, "dc:language").text = idioma

            if "procedencia" in metadata_interna:
                SubElement(dc, "dcterms:provenance").text = metadata_interna[
                    "procedencia"
                ]

            if "impresor" in metadata_interna:
                SubElement(dc, "dc:contributor").text = metadata_interna["impresor"]

            # Lo que siempre va -------------------------

            if record.get("coleccion"):
                elem = SubElement(dc, "dc:relation")
                elem.text = record["coleccion"]
                elem.set("xsi:type", "dcterms:isPartOf")

            if record.get("item_url"):
                elem = SubElement(dc, "dc:source")
                elem.text = record["item_url"]

            if record.get("portada_url"):
                elem = SubElement(dc, "dc:source")
                elem.text = record["portada_url"]
                elem.set("xsi:type", "dcterms:URI")

            SubElement(dc, "dc:identifier").text = identifier
            SubElement(dc, "dc:type").text = "archival_material_manuscript"

        case _:
            # --- VALORES POR DEFAULT
            if "titulo" in metadata_interna:
                SubElement(dc, "dc:title").text = metadata_interna["titulo"]

            SubElement(dc, "dc:identifier").text = identifier
