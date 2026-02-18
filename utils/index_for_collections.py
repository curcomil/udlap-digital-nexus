from xml.etree.ElementTree import SubElement, register_namespace

# Registrar el prefijo xsi para que ElementTree no lo redeclare en cada elemento hijo
register_namespace("xsi", "http://www.w3.org/2001/XMLSchema-instance")


def normalize_languages(value):
    LANG_MAP = [
        "español",
        "en español",
        "castellano",
        "espanol",
        "en espanol",
    ]

    if not value:
        return ""

    value = value.lower()

    if value in LANG_MAP:
        return "spa"
    else:
        return "und"


def index_4_collections(record: dict, dc: object, identifier: str):
    coleccion_nombre = record.get('coleccion')
    metadata_interna = record.get('metadata', {})

    match coleccion_nombre:
        case 'Archivo Miguel Covarrubias':
            # --- Miguel Covarrubias ---
            if "titulo" in metadata_interna:
                SubElement(dc, "dc:title").text = metadata_interna["titulo"]
            if "autor" in metadata_interna:
                SubElement(dc, "dc:creator").text = metadata_interna["autor"]
            if "descripcion" in metadata_interna:
                SubElement(dc, "dc:description").text = metadata_interna["descripcion"]

            if "tecnica" in metadata_interna:
                SubElement(dc, "discovery:local4").text = metadata_interna["tecnica"]

            if "medidas" in metadata_interna:
                SubElement(dc, "dcterms:extent").text = metadata_interna["medidas"]

            if "numero" in metadata_interna:
                elem = SubElement(dc, "dc:identifier")
                elem.text = metadata_interna["numero"]
                elem.set("xsi:type", "dcterms:URI")  # ← string plano, sin expansión

            if record.get("subcoleccion"):
                elem = SubElement(dc, "dc:relation")
                elem.text = record["subcoleccion"]
                elem.set("xsi:type", "dcterms:isPartOf")  # ← string plano, sin expansión

            if record.get("coleccion"):
                elem = SubElement(dc, "dc:relation")
                elem.text = record["coleccion"]
                elem.set("xsi:type", "dcterms:isPartOf")  # ← string plano, sin expansión

            if record.get("item_url"):
                elem = SubElement(dc, "dc:source")
                elem.text = record["item_url"]

            if record.get("portada_url"):
                elem = SubElement(dc, "dc:source")
                elem.text = record["portada_url"]
                elem.set("xsi:type", "dcterms:URI")  # ← string plano, sin expansión

            SubElement(dc, "dc:identifier").text = identifier
            SubElement(dc, "dc:type").text = "images"

        # --- AQUÍ PUEDES METER OTRO CASE PARA UNA NUEVA COLECCIÓN ---
        # case 'Nombre de la Nueva Coleccion':
        #     # Define aquí su mapeo específico...
        #     pass

        case _:
            # --- VALORES POR DEFAULT
            if "titulo" in metadata_interna:
                SubElement(dc, "dc:title").text = metadata_interna["titulo"]

            SubElement(dc, "dc:identifier").text = identifier