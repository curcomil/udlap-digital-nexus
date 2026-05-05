from datetime import datetime
from xml.dom import minidom
from xml.etree.ElementTree import Element, SubElement, tostring

from .index_for_collections import index_4_collections
from .mets_ids import HANDLE_PREFIX, make_handle, make_mets_id

DSPACE_PROFILE = "http://www.dspace.org/schema/aip/1.0/mets.xsd"
DSPACE_VERSION = "DSpace 7.6"
CUSTODIAN_NAME = "Repositorio Digital UDLAP"

NS = {
    "xmlns:mets": "http://www.loc.gov/METS/",
    "xmlns:mods": "http://www.loc.gov/mods/v3",
    "xmlns:dim": "http://www.dspace.org/xmlns/dspace/dim",
    "xmlns:xlink": "http://www.w3.org/1999/xlink",
    "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
    "xsi:schemaLocation": (
        "http://www.loc.gov/METS/ http://www.loc.gov/standards/mets/mets.xsd"
    ),
}

# Mapeo de términos dcterms a (element, qualifier) de DSpace DIM
DCTERMS_MAP = {
    # coverage
    "spatial": ("coverage", "spatial"),
    "temporal": ("coverage", "temporal"),
    # date
    "created": ("date", "created"),
    "issued": ("date", "issued"),
    "available": ("date", "available"),
    "modified": ("date", "accessioned"),
    # description
    "abstract": ("description", "abstract"),
    "tableOfContents": ("description", "tableofcontents"),
    "provenance": ("description", "provenance"),
    # format
    "extent": ("format", "extent"),
    "medium": ("format", "medium"),
    # identifier
    "identifier": ("identifier", "other"),
    "URI": ("identifier", "uri"),
    "bibliographicCitation": ("identifier", "citation"),
    # relation
    "isPartOf": ("relation", "ispartof"),
    "hasPart": ("relation", "haspart"),
    "isVersionOf": ("relation", "isversionof"),
    "hasVersion": ("relation", "hasversion"),
    "replaces": ("relation", "replaces"),
    "isReplacedBy": ("relation", "isreplacedby"),
    "requires": ("relation", "requires"),
    "isRequiredBy": ("relation", "isrequiredby"),
    "isFormatOf": ("relation", "isformatof"),
    "hasFormat": ("relation", "hasformat"),
    "references": ("relation", "references"),
    "isReferencedBy": ("relation", "isreferencedby"),
    "conformsTo": ("relation", "conformsto"),
    # rights
    "rights": ("rights", None),
    "license": ("rights", "license"),
    "accessRights": ("rights", "accessrights"),
    "rightsHolder": ("rights", "holder"),
    # title
    "alternative": ("title", "alternative"),
}

DC_QUALIFIER_MAP = {
    "isPartOf": ("relation", "ispartof"),
    "hasPart": ("relation", "haspart"),
}


# ---------------------------------------------------------------------------
# Helpers XML base
# ---------------------------------------------------------------------------


def _pretty_xml(root: Element) -> bytes:
    raw = tostring(root, encoding="unicode")
    parsed = minidom.parseString(raw)
    return parsed.toprettyxml(indent="  ", encoding="UTF-8")


def _mets_root(obj_type: str, object_id: str, label: str) -> Element:
    attrs = {
        **NS,
        "PROFILE": DSPACE_PROFILE,
        "OBJID": make_handle(object_id),
        "LABEL": label,
        "TYPE": f"DSpace {obj_type}",
        "ID": make_mets_id(obj_type, object_id),
    }
    return Element("mets:mets", attrs)


def _mets_hdr(root: Element, last_mod: str = None) -> None:
    attrs = {"CREATEDATE": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")}
    if last_mod:
        attrs["LASTMODDATE"] = last_mod
    hdr = SubElement(root, "mets:metsHdr", attrs)

    custodian = SubElement(hdr, "mets:agent", {"ROLE": "CUSTODIAN", "TYPE": "ORGANIZATION"})
    SubElement(custodian, "mets:name").text = CUSTODIAN_NAME

    creator = SubElement(
        hdr, "mets:agent", {"ROLE": "CREATOR", "TYPE": "OTHER", "OTHERTYPE": "DSpace Software"}
    )
    SubElement(creator, "mets:name").text = DSPACE_VERSION


def _add_if(parent: Element, tag: str, text: str, attrs: dict = None) -> None:
    if text and str(text).strip():
        el = SubElement(parent, tag, attrs or {})
        el.text = str(text).strip()


# ---------------------------------------------------------------------------
# dmdSec: MODS + DIM
# ---------------------------------------------------------------------------


def _dmd_mods(root: Element, record: dict, dmd_id: str) -> None:
    md = record.get("metadata", {})
    dmd = SubElement(root, "mets:dmdSec", {"ID": dmd_id})
    wrap = SubElement(dmd, "mets:mdWrap", {"MDTYPE": "MODS"})
    xml_data = SubElement(wrap, "mets:xmlData")
    mods = SubElement(xml_data, "mods:mods")

    ti = SubElement(mods, "mods:titleInfo")
    SubElement(ti, "mods:title").text = md.get("titulo", "Sin título")

    autor = md.get("autor", "").strip()
    if autor:
        name = SubElement(mods, "mods:name", {"type": "personal"})
        SubElement(name, "mods:namePart").text = autor
        role = SubElement(name, "mods:role")
        SubElement(role, "mods:roleTerm", {"type": "text"}).text = "author"

    tipo = md.get("tipo_de_objeto", "")
    if tipo:
        SubElement(mods, "mods:genre").text = tipo

    fecha = md.get("fecha") or md.get("fecha_de_publicacion", "")
    lugar = md.get("lugar") or md.get("lugar_de_impresion", "")
    editor = md.get("editor") or md.get("impresor", "")
    if fecha or lugar or editor:
        origin = SubElement(mods, "mods:originInfo")
        if fecha:
            SubElement(origin, "mods:dateIssued").text = fecha
        if lugar:
            SubElement(origin, "mods:place").text = lugar
        if editor:
            SubElement(origin, "mods:publisher").text = editor

    idioma = md.get("idioma", "")
    if idioma:
        lang_el = SubElement(mods, "mods:language")
        SubElement(lang_el, "mods:languageTerm", {"type": "text"}).text = idioma

    desc = (
        md.get("descripcion_fisica_y_notas")
        or md.get("descripcion_fisica")
        or md.get("descripcion", "")
    )
    if desc:
        SubElement(mods, "mods:abstract").text = desc

    internal_id = record.get("internal_id", "")
    num_registro = md.get("numero_de_registro", "")
    SubElement(mods, "mods:identifier", {"type": "local"}).text = internal_id or num_registro

    coleccion = record.get("coleccion", "")
    subcoleccion = record.get("subcoleccion", "")
    if coleccion:
        rel = SubElement(mods, "mods:relatedItem", {"type": "host"})
        ti_rel = SubElement(rel, "mods:titleInfo")
        SubElement(ti_rel, "mods:title").text = coleccion
        if subcoleccion:
            ti_sub = SubElement(rel, "mods:titleInfo", {"type": "alternative"})
            SubElement(ti_sub, "mods:title").text = subcoleccion


def _dmd_dim(root: Element, record: dict, dmd_id: str) -> None:
    internal_id = record.get("internal_id", "")

    dc_container = Element("dc_container")
    index_4_collections(record, dc_container, internal_id)

    dmd = SubElement(root, "mets:dmdSec", {"ID": dmd_id})
    wrap = SubElement(dmd, "mets:mdWrap", {"MDTYPE": "OTHER", "OTHERMDTYPE": "DIM"})
    xml_data = SubElement(wrap, "mets:xmlData")
    dim = SubElement(xml_data, "dim:dim", {"dspaceType": "ITEM"})

    for dc_el in dc_container:
        tag = dc_el.tag
        value = (dc_el.text or "").strip()
        if not value:
            continue

        if ":" in tag:
            prefix, local = tag.split(":", 1)
        else:
            prefix, local = "dc", tag

        mdschema = "dc"

        if prefix == "dcterms" and local in DCTERMS_MAP:
            element, qualifier = DCTERMS_MAP[local]
        elif prefix == "dcterms":
            element, qualifier = "description", local.lower()
        else:
            if local in DC_QUALIFIER_MAP:
                element, qualifier = DC_QUALIFIER_MAP[local]
            else:
                element, qualifier = local, None

        xsi_type = dc_el.get("{http://www.w3.org/2001/XMLSchema-instance}type", "")
        if xsi_type and not qualifier:
            xsi_local = xsi_type.split(":")[-1].lower()
            qualifier = xsi_local if xsi_local != element else None

        attrs = {"mdschema": mdschema, "element": element}
        if qualifier:
            attrs["qualifier"] = qualifier

        SubElement(dim, "dim:field", attrs).text = value


# ---------------------------------------------------------------------------
# amdSec
# ---------------------------------------------------------------------------


def _amd_item(root: Element, record: dict, amd_id: str) -> None:
    md = record.get("metadata", {})
    amd = SubElement(root, "mets:amdSec", {"ID": amd_id})
    src = SubElement(amd, "mets:sourceMD", {"ID": f"sourceMD_{amd_id}"})
    wrap = SubElement(src, "mets:mdWrap", {"MDTYPE": "OTHER", "OTHERMDTYPE": "AIP-TECHMD"})
    xml_data = SubElement(wrap, "mets:xmlData")
    dim = SubElement(xml_data, "dim:dim", {"dspaceType": "ITEM"})

    def field(element: str, text: str, qualifier: str = None) -> None:
        if not text or not str(text).strip():
            return
        attrs = {"mdschema": "dc", "element": element}
        if qualifier:
            attrs["qualifier"] = qualifier
        SubElement(dim, "dim:field", attrs).text = str(text).strip()

    field("identifier", record.get("internal_id"), "uri")
    field("date", md.get("disponible_desde"), "available")
    field("date", md.get("mdate"), "accessioned")
    field("relation", record.get("coleccion"), "ispartof")


def _amd_bitstream(
    root: Element,
    file_id: str,
    amd_id: str,
    file_name: str,
    md5: str,
    size: int,
    mimetype: str,
) -> None:
    amd = SubElement(root, "mets:amdSec", {"ID": amd_id})
    tech = SubElement(amd, "mets:techMD", {"ID": f"techMD_{amd_id}"})
    wrap = SubElement(tech, "mets:mdWrap", {"MDTYPE": "PREMIS:OBJECT"})
    xml_data = SubElement(wrap, "mets:xmlData")

    obj = SubElement(
        xml_data,
        "premis:object",
        {"xmlns:premis": "info:lc/xmlns/premis-v2", "xsi:type": "premis:file"},
    )
    oid = SubElement(obj, "premis:objectIdentifier")
    SubElement(oid, "premis:objectIdentifierType").text = "local"
    SubElement(oid, "premis:objectIdentifierValue").text = file_name

    chars = SubElement(obj, "premis:objectCharacteristics")
    fix = SubElement(chars, "premis:fixity")
    SubElement(fix, "premis:messageDigestAlgorithm").text = "MD5"
    SubElement(fix, "premis:messageDigest").text = md5
    SubElement(chars, "premis:size").text = str(size)
    fmt = SubElement(chars, "premis:format")
    fmt_des = SubElement(fmt, "premis:formatDesignation")
    SubElement(fmt_des, "premis:formatName").text = mimetype

    SubElement(obj, "premis:originalName").text = file_name


# ---------------------------------------------------------------------------
# Builders públicos: ITEM, COLLECTION, COMMUNITY
# ---------------------------------------------------------------------------


def build_item_mets(
    record: dict,
    item_handle_id: str,
    collection_handle_id: str,
    file_data: dict[str, tuple[bytes, str, int]],
) -> bytes:
    md = record.get("metadata", {})
    root = _mets_root("ITEM", item_handle_id, md.get("titulo", "Sin título"))
    _mets_hdr(root, md.get("mdate", ""))

    _dmd_mods(root, record, "dmdSec_1")
    _dmd_dim(root, record, "dmdSec_2")
    _amd_item(root, record, "amd_item")

    if "content" in record:
        all_pages = [
            {
                "file_name": page["file_name"],
                "section_name": section["name"],
                "section_number": section["number"],
                "page_number": page["number"],
            }
            for section in record["content"]
            for page in section.get("pages", [])
        ]
    else:
        # Item de imagen única: las páginas se derivan de lo que fue descargado
        all_pages = [
            {"file_name": fn, "section_name": None, "section_number": 0, "page_number": 1}
            for fn in file_data.keys()
        ]

    for i, page in enumerate(all_pages, start=1):
        fn = page["file_name"]
        _, md5, size = file_data.get(fn, (None, "unknown", 0))
        _amd_bitstream(root, f"file_{i}", f"amd_file_{i}", fn, md5, size, "image/jpeg")

    file_sec = SubElement(root, "mets:fileSec")
    grp_original = SubElement(file_sec, "mets:fileGrp", {"USE": "ORIGINAL"})
    for i, page in enumerate(all_pages, start=1):
        fn = page["file_name"]
        _, md5, size = file_data.get(fn, (None, "unknown", 0))
        file_el = SubElement(
            grp_original,
            "mets:file",
            {
                "ID": f"file_{i}",
                "MIMETYPE": "image/jpeg",
                "SIZE": str(size),
                "CHECKSUM": md5,
                "CHECKSUMTYPE": "MD5",
                "SEQ": str(i),
                "ADMID": f"amd_file_{i}",
            },
        )
        SubElement(file_el, "mets:FLocat", {"LOCTYPE": "URL", "xlink:href": fn})

    struct_logical = SubElement(
        root, "mets:structMap", {"TYPE": "LOGICAL", "LABEL": "DSpace Object"}
    )
    top_div = SubElement(
        struct_logical,
        "mets:div",
        {"TYPE": "DSpace Object Contents", "DMDID": "dmdSec_1 dmdSec_2", "ADMID": "amd_item"},
    )

    sections: dict[str, list] = {}
    for i, page in enumerate(all_pages, start=1):
        sec_key = f"{page['section_number']}_{page['section_name']}"
        sections.setdefault(sec_key, []).append((i, page))

    for sec_key, pages_in_sec in sections.items():
        sec_name = pages_in_sec[0][1]["section_name"]
        if sec_name:
            container = SubElement(
                top_div, "mets:div", {"TYPE": "DSpace BITSTREAM", "LABEL": sec_name}
            )
        else:
            container = top_div
        for file_seq, _ in pages_in_sec:
            SubElement(container, "mets:fptr", {"FILEID": f"file_{file_seq}"})

    struct_parent = SubElement(
        root, "mets:structMap", {"TYPE": "LOGICAL", "LABEL": "Parent"}
    )
    parent_div = SubElement(struct_parent, "mets:div", {"TYPE": "AIP Parent Link"})
    SubElement(
        parent_div,
        "mets:mptr",
        {"LOCTYPE": "HANDLE", "xlink:href": f"{HANDLE_PREFIX}/{collection_handle_id}"},
    )

    return _pretty_xml(root)


def build_collection_mets(
    col_name: str,
    col_handle_id: str,
    community_handle_id: str,
    item_handle_ids: list[str],
) -> bytes:
    root = _mets_root("COLLECTION", col_handle_id, col_name)
    _mets_hdr(root)

    dmd = SubElement(root, "mets:dmdSec", {"ID": "dmdSec_1"})
    wrap = SubElement(dmd, "mets:mdWrap", {"MDTYPE": "OTHER", "OTHERMDTYPE": "DIM"})
    xml_data = SubElement(wrap, "mets:xmlData")
    dim = SubElement(xml_data, "dim:dim", {"dspaceType": "COLLECTION"})
    SubElement(dim, "dim:field", {"mdschema": "dc", "element": "title"}).text = col_name
    SubElement(
        dim, "dim:field", {"mdschema": "dc", "element": "identifier", "qualifier": "uri"}
    ).text = make_handle(col_handle_id)

    SubElement(root, "mets:amdSec", {"ID": "amd_col"})

    struct = SubElement(root, "mets:structMap", {"TYPE": "LOGICAL", "LABEL": "DSpace Object"})
    top_div = SubElement(struct, "mets:div", {"TYPE": "DSpace Object Contents"})
    for item_id in item_handle_ids:
        item_div = SubElement(top_div, "mets:div", {"TYPE": "DSpace ITEM"})
        SubElement(item_div, "mets:mptr", {"LOCTYPE": "HANDLE", "xlink:href": item_id})

    struct_parent = SubElement(root, "mets:structMap", {"TYPE": "LOGICAL", "LABEL": "Parent"})
    parent_div = SubElement(struct_parent, "mets:div", {"TYPE": "AIP Parent Link"})
    SubElement(
        parent_div,
        "mets:mptr",
        {"LOCTYPE": "HANDLE", "xlink:href": f"{HANDLE_PREFIX}/{community_handle_id}"},
    )

    return _pretty_xml(root)


def build_community_mets(
    com_name: str, com_handle_id: str, collection_handle_ids: list[str]
) -> bytes:
    root = _mets_root("COMMUNITY", com_handle_id, com_name)
    _mets_hdr(root)

    dmd = SubElement(root, "mets:dmdSec", {"ID": "dmdSec_1"})
    wrap = SubElement(dmd, "mets:mdWrap", {"MDTYPE": "OTHER", "OTHERMDTYPE": "DIM"})
    xml_data = SubElement(wrap, "mets:xmlData")
    dim = SubElement(xml_data, "dim:dim", {"dspaceType": "COMMUNITY"})
    SubElement(dim, "dim:field", {"mdschema": "dc", "element": "title"}).text = com_name
    SubElement(
        dim, "dim:field", {"mdschema": "dc", "element": "identifier", "qualifier": "uri"}
    ).text = make_handle(com_handle_id)

    SubElement(root, "mets:amdSec", {"ID": "amd_com"})

    struct = SubElement(root, "mets:structMap", {"TYPE": "LOGICAL", "LABEL": "DSpace Object"})
    top_div = SubElement(struct, "mets:div", {"TYPE": "DSpace Object Contents"})
    for col_id in collection_handle_ids:
        col_div = SubElement(top_div, "mets:div", {"TYPE": "DSpace COLLECTION"})
        SubElement(col_div, "mets:mptr", {"LOCTYPE": "HANDLE", "xlink:href": col_id})

    return _pretty_xml(root)
