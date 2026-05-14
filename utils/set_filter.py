def setfilter(filtro: str, data: dict | None) -> list:
    _, _, sufijo = filtro.partition(":")
    res = []
    if data:
        res.append(data["coleccion"]["name_collection"])
        if sufijo:
            for sub in data.get("subcolecciones", []):
                if sub["setspec_subcollection"] == sufijo:
                    res.append(sub["name_subcollection"])
                    break
    return res
