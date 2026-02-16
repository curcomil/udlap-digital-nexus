import re
import unicodedata
from flask import current_app as app
from db import MongoDBConnection_OAI

repo_items = MongoDBConnection_OAI("items")

def normalizar_setspec(texto: str) -> str:
    if not texto:
        return ""
    
    texto = texto.lower()
    texto = (
        unicodedata.normalize("NFKD", texto)
        .encode("ascii", "ignore")
        .decode("ascii")
    )
    texto = re.sub(r"[^a-z0-9]+", "_", texto)
    return texto.strip("_")


def parse_oai_date(date_str: str) -> str | None:
    try:
        if not date_str:
            return None
        return date_str.split(" ")[0]
    except Exception:
        return None


def build_list_identifiers(
    base_url: str,
    metadata_prefix: str,
    set_filter: list | None = None,
    date_from: str | None = None,
    date_until: str | None = None,
) -> list[dict]:

    if metadata_prefix != "oai_dc":
        raise ValueError("cannotDisseminateFormat")

    headers: list[dict] = []

    if set_filter:
        col_id = set_filter[0]
        sub_id = set_filter[1] if len(set_filter) > 1 else None
        items = repo_items.find_items(col_id, sub_id)
    else:
        items = repo_items.get_all()

    if not items:
        return []

    for item in items:
        internal_id = item.get("internal_id")
        mdate_raw = item.get("metadata", {}).get("mdate")
        
        col_raw = item.get("coleccion")
        sub_raw = item.get("subcoleccion")


        if not internal_id or not mdate_raw or not col_raw:
            continue

        datestamp = parse_oai_date(mdate_raw)
        if not datestamp:
            continue

        if date_from and datestamp < date_from:
            continue
        if date_until and datestamp > date_until:
            continue

  
        col_norm = normalizar_setspec(col_raw)
        sub_norm = normalizar_setspec(sub_raw)

        setspec_final = f"{col_norm}:{sub_norm}" if sub_norm else col_norm

        headers.append(
            {
                "identifier": f"oai:{base_url}:{internal_id}",
                "datestamp": datestamp,
                "setSpec": setspec_final,
            }
        )

    return headers