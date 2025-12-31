import os
import json
from datetime import datetime
import unicodedata
import re
from flask import current_app as app


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


def build_list_identifiers(
    data_path: str,
    base_url: str,
    metadata_prefix: str,
    set_filter: str | None = None,
    date_from: str | None = None,
    date_until: str | None = None,
) -> list[dict]:

    if metadata_prefix != "oai_dc":
        raise ValueError("cannotDisseminateFormat")

    headers: list[dict] = []

    for file in os.listdir(data_path):
        if not file.endswith(".json"):
            continue

        with open(os.path.join(data_path, file), "r", encoding="utf-8") as f:
            collection_data = json.load(f)

        collection_name = normalizar_setspec(collection_data.get("coleccion", file))

        for sub in collection_data.get("subcolecciones", []):
            sub_name = normalizar_setspec(sub.get("name"))
            set_spec = f"{collection_name}:{sub_name}"

            # filtro por set (solo hojas)
            if set_filter and set_filter != set_spec:
                continue

            items = sub.get("items", [])
            for idx, item in enumerate(items):
                # Ignorar items que no sean diccionarios
                if not isinstance(item, dict):
                    app.logger.warning(
                        f"Item inválido en archivo={file}, "
                        f"subcolección={sub.get('name')}, "
                        f"index={idx}, "
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

                # filtros de fecha
                if date_from and datestamp < date_from:
                    continue
                if date_until and datestamp > date_until:
                    continue

                headers.append(
                    {
                        "identifier": f"oai:{base_url}:{internal_id}",
                        "datestamp": datestamp,
                        "setSpec": set_spec,
                    }
                )

    return headers
