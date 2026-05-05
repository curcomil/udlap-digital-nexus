from db import MongoDBConnection_OAI


def setfilter(filtro: str):
    prefijo, _, sufijo = filtro.partition(":")

    repo_estructura = MongoDBConnection_OAI("estructura")
    data = repo_estructura.set_filter(prefijo, sufijo if sufijo else None)

    res = []
    if data:
        nombre_col = data["coleccion"]["name_collection"]
        res.append(nombre_col)

        if sufijo:
            for sub in data.get("subcolecciones", []):
                if sub["setspec_subcollection"] == sufijo:
                    res.append(sub["name_subcollection"])
                    break

    return res
