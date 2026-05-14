import re
import unicodedata


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
    items: list,
    date_from: str | None = None,
    date_until: str | None = None,
) -> list[dict]:

    if metadata_prefix != "oai_dc":
        raise ValueError("cannotDisseminateFormat")

    if not items:
        return []

    headers: list[dict] = []

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
