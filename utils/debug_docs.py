"""Autodocumentación de los endpoints raíz para el modo debug.

Cuando ``ENVIROMENT == "debug"`` cada función *root* de un blueprint devuelve
un JSON que describe el grupo de endpoints y qué hace cada uno. Ese contenido
vive aquí, no en las rutas:

- ``DEBUG_ENDPOINTS`` mapea el nombre de un endpoint raíz a la función que
  construye su respuesta.
- ``get_debug_docs(nombre, **kwargs)`` hace el match por nombre y delega en esa
  función, pasándole los datos dinámicos que haga falta
  (``coleccion=<nombre>`` para la ruta por colección, ``db_connection=<ping>``
  para el root de la API).
"""


def _api_root(db_connection=None, **_):
    return {
        "message": "API root endpoint.",
        "context": "Punto de entrada de la API. Expone tres grupos bajo /api y, en debug, hace ping a MongoDB (db_connection).",
        "db_connection": db_connection,
        "available_endpoints": [
            {
                "path": "/api/auth",
                "context": "Registro y login de usuarios XMLibris. Emite el JWT (8 h) que usa el resto de la API.",
            },
            {
                "path": "/api/users",
                "context": "CRUD de usuarios sobre xmlibris.users. Requiere JWT; casi todo exige rol admin.",
            },
            {
                "path": "/api/xmlibris",
                "context": "Lectura y edición de carpetas e items de cada colección en la base udlap, y alta de nuevas colecciones.",
            },
        ],
    }


def _auth_root(**_):
    return {
        "message": "Auth root endpoint.",
        "context": "Autenticación de XMLibris. El registro solo funciona para correos previamente dados de alta en xmlibris.users; el login devuelve un JWT válido 8 h.",
        "available_endpoints": [
            {
                "path": "/api/auth/xmlibris/register",
                "method": "POST",
                "context": "Body JSON {username, password, email}. Busca el correo en xmlibris.users: 403 si no está en la whitelist, 409 si ese correo ya tiene username o el username está tomado. Si procede, hashea la contraseña y hace $set de username y password sobre el documento existente. 201 al crear.",
            },
            {
                "path": "/api/auth/xmlibris/login",
                "method": "POST",
                "context": "Body JSON {username, password} (username se compara contra username o email). 404 si no existe, 403 si nunca completó el registro o isActive=false, 401 si la contraseña no coincide. Devuelve {token, user:{username,name,role,_id}} con JWT de 8 h.",
            },
        ],
    }


def _users_root(**_):
    return {
        "message": "Users root endpoint.",
        "note": "Todos los endpoints requieren JWT. Admin: la mayoría. Digitalizer: /getcoordinators.",
        "context": "Administración de usuarios sobre xmlibris.users. Todos los endpoints requieren JWT; la mayoría exige rol admin, salvo /getcoordinators que exige rol digitizer.",
        "available_endpoints": [
            {
                "path": "/api/users/getusers",
                "method": "GET",
                "auth": "admin",
                "context": "Sin body. Devuelve todos los documentos de xmlibris.users (404 si vacía). Cada fila se sanea: _id a string y password reemplazado por un booleano 'tiene contraseña'.",
            },
            {
                "path": "/api/users/create",
                "method": "POST",
                "auth": "admin",
                "context": "Body JSON insertado tal cual con insert_one como documento de usuario (sin hashear contraseña ni validar whitelist). Traduce fallos de validación de esquema de Mongo a 'Faltan campos requeridos: <campos>'. 201 al crear.",
            },
            {
                "path": "/api/users/<user_id>",
                "method": "PATCH",
                "auth": "admin",
                "context": "user_id debe ser ObjectId válido (400 si no). Aplica el body completo como $set sobre el usuario, sin lista blanca de campos. 200, o 404 si no existe.",
            },
            {
                "path": "/api/users/<user_id>",
                "method": "DELETE",
                "auth": "admin",
                "context": "user_id ObjectId válido (400 si no). Elimina permanentemente el documento del usuario. 200, o 404.",
            },
            {
                "path": "/api/users/reset_credentials/<user_id>",
                "method": "DELETE",
                "auth": "admin",
                "context": "user_id ObjectId válido (400 si no). Hace $set de username=None y password=None, obligando al usuario a repetir /auth/xmlibris/register sin perder su entrada de whitelist. 200, o 404.",
            },
            {
                "path": "/api/users/getcoordinators",
                "method": "GET",
                "auth": "digitalizer",
                "context": "Sin body. Devuelve coordinadores activos (role=coordinator, isActive=true); 404 si no hay. Se quitan de cada fila isActive, accessibleRoles, assignedCollections, role y password. El decorador exige claim role=='digitizer'.",
            },
        ],
    }


def _xmlibris_root(**_):
    return {
        "message": "XMLibris root endpoint.",
        "context": "Gestión de colecciones XMLibris. El <coleccion> de la URL es el nombre de una colección dentro de la base fija udlap; los documentos se distinguen por el campo type (carpeta | item | collection).",
        "available_endpoints": [
            {
                "path": "/api/xmlibris/<coleccion>",
                "method": "GET",
                "context": "Sub-índice de una colección. En debug devuelve la lista de operaciones disponibles para esa colección.",
            },
            {
                "path": "/api/xmlibris/<coleccion>/carpetas",
                "method": "GET",
                "context": "Devuelve un array con todos los documentos type=carpeta de la colección (find({'type': 'carpeta'})). 404 con data:[] si no hay.",
            },
            {
                "path": "/api/xmlibris/<coleccion>/carpeta/<carpeta_id>",
                "method": "GET",
                "context": "carpeta_id ObjectId válido (400 si no). Devuelve el documento de carpeta con ese _id y type=carpeta, o 404 'Carpeta no encontrada'.",
            },
            {
                "path": "/api/xmlibris/<coleccion>/carpeta/<carpeta_id>",
                "method": "PUT",
                "context": "carpeta_id ObjectId válido y body JSON no vacío (400). Aplica el body completo como $set sobre la carpeta y devuelve el documento actualizado; 404 si no existe o sin cambios.",
            },
            {
                "path": "/api/xmlibris/<coleccion>/items/<carpeta_id>",
                "method": "GET",
                "context": "carpeta_id se usa como string (sin cast a ObjectId). Devuelve todos los type=item cuyo papiro_data.father_id coincide; 404 con data:[] si no hay.",
            },
            {
                "path": "/api/xmlibris/<coleccion>/item/<item_id>",
                "method": "PUT",
                "context": "item_id ObjectId válido y body JSON no vacío (400). Aplica el body completo como $set sobre el item (type=item) y devuelve el documento actualizado; 404 si no existe o sin cambios.",
            },
            {
                "path": "/api/xmlibris/<coleccion>/findbyfilter",
                "method": "POST",
                "context": "Body JSON {type, filtro, query}. Mapea filtro a un campo real de Mongo (titulo->dc_metadata.titulo, autor->dc_metadata.autor, tipologia->papiro_data.tipo_de_objeto, keywords->papiro_data.keywords, ...), hace match case-insensitive por regex sobre query y adjunta la carpeta padre vía $lookup self-join. Con filtro=subcoleccion_normalizada normaliza query (minúsculas, sin acentos, no-[a-z0-9]->_). Devuelve los items con carpeta_padre; 404 'Sin coincidencias' si nada.",
            },
            {
                "path": "/api/xmlibris/newcollection",
                "method": "POST",
                "auth": "coordinator",
                "context": "Requiere JWT role=coordinator. Body JSON: extrae user y new_collection_name (default 'general') y el resto es el payload. Hace insert_one del payload en la colección indicada dentro de udlap. Traduce fallos de validación de esquema a 'Faltan campos requeridos'. 201 al crear. (Nota: el controller arma un sobre de workflow con historial pero hoy inserta el payload crudo.)",
            },
        ],
    }


def _coleccion_root(coleccion="<coleccion>", **_):
    return {
        "message": f"{coleccion} root endpoint.",
        "context": f"Operaciones sobre la colección '{coleccion}' (colección de Mongo dentro de la base 'udlap'). Los documentos se distinguen por el campo type: carpeta (agrupador) e item (registro).",
        "available_endpoints": [
            {
                "path": f"/api/xmlibris/{coleccion}/carpetas",
                "method": "GET",
                "context": "Devuelve un array con todos los documentos type=carpeta de la colección (find({'type': 'carpeta'})). 404 con data:[] si no hay.",
            },
            {
                "path": f"/api/xmlibris/{coleccion}/carpeta/<carpeta_id>",
                "method": "GET",
                "context": "carpeta_id ObjectId válido (400 si no). Devuelve el documento de carpeta con ese _id y type=carpeta, o 404 'Carpeta no encontrada'.",
            },
            {
                "path": f"/api/xmlibris/{coleccion}/carpeta/<carpeta_id>",
                "method": "PUT",
                "context": "carpeta_id ObjectId válido y body JSON no vacío (400). Aplica el body completo como $set sobre la carpeta y devuelve el documento actualizado; 404 si no existe o sin cambios.",
            },
            {
                "path": f"/api/xmlibris/{coleccion}/items/<carpeta_id>",
                "method": "GET",
                "context": "carpeta_id se usa como string (sin cast a ObjectId). Devuelve todos los type=item cuyo papiro_data.father_id coincide; 404 con data:[] si no hay.",
            },
            {
                "path": f"/api/xmlibris/{coleccion}/item/<item_id>",
                "method": "PUT",
                "context": "item_id ObjectId válido y body JSON no vacío (400). Aplica el body completo como $set sobre el item (type=item) y devuelve el documento actualizado; 404 si no existe o sin cambios.",
            },
            {
                "path": f"/api/xmlibris/{coleccion}/findbyfilter",
                "method": "POST",
                "context": "Body JSON {type, filtro, query}. Mapea filtro a un campo real de Mongo (titulo->dc_metadata.titulo, autor->dc_metadata.autor, tipologia->papiro_data.tipo_de_objeto, keywords->papiro_data.keywords, ...), hace match case-insensitive por regex sobre query y adjunta la carpeta padre vía $lookup self-join. Con filtro=subcoleccion_normalizada normaliza query (minúsculas, sin acentos, no-[a-z0-9]->_). Devuelve los items con carpeta_padre; 404 'Sin coincidencias' si nada.",
            },
        ],
    }


DEBUG_ENDPOINTS = {
    "api": _api_root,
    "auth": _auth_root,
    "users": _users_root,
    "xmlibris": _xmlibris_root,
    "coleccion": _coleccion_root,
}


def get_debug_docs(endpoint, **kwargs):
    """Devuelve la respuesta de autodocumentación del endpoint raíz indicado.

    ``endpoint`` es una clave de ``DEBUG_ENDPOINTS`` ("api", "auth", "users",
    "xmlibris", "coleccion"). Los ``kwargs`` extra se reenvían al builder
    (p. ej. ``coleccion``, ``db_connection``). Si el nombre no existe devuelve
    un dict de error en vez de lanzar.
    """
    builder = DEBUG_ENDPOINTS.get(endpoint)
    if builder is None:
        return {"message": f"Endpoint de debug desconocido: {endpoint}"}
    return builder(**kwargs)
