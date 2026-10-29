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
                "context": "Lectura y edición de subcolecciones e items de cada colección en la base 'xmlibris' (colecciones 'colecciones' e 'items'), y alta de nuevas colecciones.",
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
        "context": "Gestión de colecciones XMLibris sobre la base 'xmlibris'. El <coleccion> de la URL es el setspec_collection de la colección; los items viven en la colección 'items' y las carpetas son las subcolecciones embebidas en el registro 'colecciones'.",
        "available_endpoints": [
            {
                "path": "/api/xmlibris/getallcollections",
                "method": "GET",
                "context": "Sin body. Devuelve todas las colecciones del registro (coleccion 'colecciones') omitiendo los campos schema y exportacion_fija, que solo viajan en el detalle. 404 con data:[] si no hay ninguna.",
            },
            {
                "path": "/api/xmlibris/getcollection/<internal_id>",
                "method": "GET",
                "context": "internal_id es el de coleccion.internal_id. Devuelve el documento COMPLETO de esa colección, incluidos schema y exportacion_fija. 404 'Colección no encontrada' si no existe.",
            },
            {
                "path": "/api/xmlibris/<coleccion>",
                "method": "GET",
                "context": "Sub-índice de una colección. En debug devuelve la lista de operaciones disponibles para esa colección.",
            },
            {
                "path": "/api/xmlibris/<coleccion>/subcolecciones",
                "method": "GET",
                "context": "Sin body. Devuelve el arreglo subcolecciones embebido en el registro de la colección (name_subcollection, setspec_subcollection, internal_id, app, status). 404 'Colección no encontrada' si la colección no existe; 200 con data:[] si no hay subcolecciones. Tope de 100 resultados por consulta: el bloque `pagination` (limit, returned, has_more) avisa si quedaron más.",
            },
            {
                "path": "/api/xmlibris/<coleccion>/subcoleccion/<internal_id>",
                "method": "PUT",
                "context": "Body JSON con rutas con punto, ej. {\"name_subcollection\": \"...\", \"app.notas\": \"...\"}. internal_id es el de la subcolección (19 dígitos). Actualiza la subcolección EMBEBIDA en el registro 'colecciones' con un solo find_one_and_update y arrayFilters sobre subcolecciones.$[sub]. Campos permitidos: name_subcollection, status, app.notas, app.miniatura y app.referencia_externa; internal_id y setspec_subcollection NO son editables (son la identidad y el vínculo desde parents.subcoleccion de los items). Cualquier otro campo devuelve 400 'Campos no editables: ...'. Devuelve la subcolección actualizada; 404 'Subcolección no encontrada'. REQUIERE JWT con role admin, coordinator o digitizer (403 si no).",
            },
            {
                "path": "/api/xmlibris/<coleccion>/items/<subcoleccion>",
                "method": "GET",
                "context": "Sin body. Devuelve los items de la subcolección desde la colección 'items', filtrando por parents.coleccion.setspec_collection + parents.subcoleccion.setspec_subcollection (el slug). Cada item es el documento nuevo completo (internal_id, is_published, parents, metadata, app, content). metadata.portada se reescribe como la ruta <coleccion>/<subcoleccion>/<internal_id>/<archivo>, SIN el prefijo getfile (el cliente la usa contra /api/xmlibris/getfile/); si el item no trae portada se deja tal cual. 200 con data:[] si la subcolección no tiene items. Tope de 100 resultados por consulta: el bloque `pagination` (limit, returned, has_more) avisa si quedaron más.",
            },
            {
                "path": "/api/xmlibris/getfile/<coleccion>/<subcoleccion>/<internal_id>/<archivo>",
                "method": "GET",
                "context": "Sin body. Entrega el binario (imagen o PDF) desde FILES_ROOT/<coleccion>/<subcoleccion>/<internal_id>/<archivo>. 404 'Archivo no encontrado' si no existe; 400 'Ruta inválida' si algún componente intenta salir de la raíz.",
            },
            {
                "path": "/api/xmlibris/<coleccion>/item/<internal_id>",
                "method": "PUT",
                "context": "Body JSON con rutas con punto, ej. {\"metadata.titulo\": \"...\", \"app.notas\": \"...\", \"is_published\": true}. internal_id es el del item (19 dígitos, sin validación de formato). Aplica $set sobre el documento de 'items' filtrando por internal_id + parents.coleccion.setspec_collection y devuelve el documento actualizado con metadata.portada ya reescrita. Solo acepta rutas de un nivel bajo metadata. o app., más is_published; cualquier otra devuelve 400 'Campos no editables: ...'. 404 'Item no encontrado'. REQUIERE JWT con role admin, coordinator o digitizer (403 si no).",
            },
            {
                "path": "/api/xmlibris/newitem",
                "method": "POST",
                "auth": "admin | coordinator | digitizer",
                "context": "Alta de un item nuevo en estado pending. Acepta JSON o multipart/form-data. En multipart el campo 'data' lleva el JSON del item y los archivos van en 'files' (o 'file'). El JSON requiere parents (solo se usa parents.coleccion.internal_id para resolver la colección; los datos de parents se reconstruyen desde el registro real), origen (acervo|tesis), metadata validada contra el schema de la colección, libro (bool) y estructura (secciones/cantidades del libro). El controller deja los binarios en FILES_ROOT/pendiente/<coleccion>/<subcoleccion>/<internal_id>/ y guarda content con la forma plana o paginada.",
            },
            {
                "path": "/api/xmlibris/newcollection",
                "method": "POST",
                "auth": "coordinator",
                "context": "NO SE VA A CONSTRUIR (decisión tomada). El endpoint sigue wired y roto: inserta el payload crudo en xmlibris.<new_collection_name> y descarta el sobre de aprobación que arma el controller (status, history, reviewedByCoordinator...). Requiere JWT role=coordinator. Queda pendiente decidir si se elimina por completo (ruta + controller + método de db + esta entrada + la llamada new_collection() del frontend) o se deja como está.",
            },
        ],
    }


def _coleccion_root(coleccion="<coleccion>", **_):
    return {
        "message": f"{coleccion} root endpoint.",
        "context": f"Operaciones sobre la colección '{coleccion}' en la base 'xmlibris': las subcolecciones viven embebidas en el registro 'colecciones' y los items en la colección 'items' (vinculados por parents.coleccion.setspec_collection y parents.subcoleccion.setspec_subcollection).",
        "available_endpoints": [
            {
                "path": f"/api/xmlibris/{coleccion}/subcolecciones",
                "method": "GET",
                "context": "Sin body. Devuelve el arreglo subcolecciones embebido en el registro de la colección (name_subcollection, setspec_subcollection, internal_id, app, status). 404 'Colección no encontrada' si la colección no existe; 200 con data:[] si no hay subcolecciones. Tope de 100 resultados por consulta: el bloque `pagination` (limit, returned, has_more) avisa si quedaron más.",
            },
            {
                "path": f"/api/xmlibris/{coleccion}/subcoleccion/<internal_id>",
                "method": "PUT",
                "context": "Body JSON con rutas con punto, ej. {\"name_subcollection\": \"...\", \"app.notas\": \"...\"}. internal_id es el de la subcolección (19 dígitos). Actualiza la subcolección EMBEBIDA en el registro 'colecciones' con un solo find_one_and_update y arrayFilters sobre subcolecciones.$[sub]. Campos permitidos: name_subcollection, status, app.notas, app.miniatura y app.referencia_externa; internal_id y setspec_subcollection NO son editables (son la identidad y el vínculo desde parents.subcoleccion de los items). Cualquier otro campo devuelve 400 'Campos no editables: ...'. Devuelve la subcolección actualizada; 404 'Subcolección no encontrada'. REQUIERE JWT con role admin, coordinator o digitizer (403 si no).",
            },
            {
                "path": f"/api/xmlibris/{coleccion}/items/<subcoleccion>",
                "method": "GET",
                "context": "Sin body. Devuelve los items de la subcolección desde la colección 'items', filtrando por parents.coleccion.setspec_collection + parents.subcoleccion.setspec_subcollection (el slug). Cada item es el documento nuevo completo (internal_id, is_published, parents, metadata, app, content). metadata.portada se reescribe como la ruta <coleccion>/<subcoleccion>/<internal_id>/<archivo>, SIN el prefijo getfile (el cliente la usa contra /api/xmlibris/getfile/); si el item no trae portada se deja tal cual. 200 con data:[] si la subcolección no tiene items. Tope de 100 resultados por consulta: el bloque `pagination` (limit, returned, has_more) avisa si quedaron más.",
            },
            {
                "path": f"/api/xmlibris/{coleccion}/item/<internal_id>",
                "method": "PUT",
                "context": "Body JSON con rutas con punto, ej. {\"metadata.titulo\": \"...\", \"app.notas\": \"...\", \"is_published\": true}. internal_id es el del item (19 dígitos, sin validación de formato). Aplica $set sobre el documento de 'items' filtrando por internal_id + parents.coleccion.setspec_collection y devuelve el documento actualizado con metadata.portada ya reescrita. Solo acepta rutas de un nivel bajo metadata. o app., más is_published; cualquier otra devuelve 400 'Campos no editables: ...'. 404 'Item no encontrado'. REQUIERE JWT con role admin, coordinator o digitizer (403 si no).",
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
