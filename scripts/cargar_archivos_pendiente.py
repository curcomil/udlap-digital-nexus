"""Prepara los binarios de un item nuevo en la zona ``pendiente``.

El script no inserta en Mongo: solo deja los archivos en disco y devuelve el
arreglo ``content`` con la MISMA forma que usa ``xmlibris.items``.

En ambos flujos ``content`` es una **lista con los nombres** de los archivos.

Contrato de entrada
-------------------
``libro=True``
    Se espera un ``.zip``: en ``files`` o ya subido en ``FILES_ROOT/tmp`` con
    ``zip_upload_id``. Las entradas deben estar en la raíz del ZIP y ya
    numeradas (``0001.jpg``...), porque el nombre es el orden. Solo se extraen
    ``.jpg``, ``.jpeg``, ``.png`` y ``.pdf``; el resto se ignora.

``libro=False``
    Se espera **exactamente un archivo** ``.jpg``, ``.jpeg``, ``.png`` o
    ``.pdf``. Si llega más de uno se rechaza. El archivo se guarda con su nombre
    normalizado por ``normalizar_setspec`` y conserva la extensión original.
"""

from __future__ import annotations

import io
import logging
import mimetypes
import os
import re
import shutil
import uuid
import zipfile

from utils.general import normalizar_setspec

logger = logging.getLogger(__name__)

_BUFFER_ESCRITURA = 1024 * 1024
_EXTENSION_VALIDA = re.compile(r"^\.[a-z0-9]{1,10}$")

# Extensiones aceptadas para archivos de un item.
_EXTENSIONES_ACEPTADAS = frozenset({".jpg", ".jpeg", ".png", ".pdf"})


class ErrorCargaArchivos(Exception):
    """Error controlado de validación o de escritura en disco."""

    def __init__(self, message: str, status: int = 400):
        super().__init__(message)
        self.message = message
        self.status = status


def _limpiar_nombre(nombre) -> str:
    """Deja solo el nombre base, sin rutas ni caracteres de control."""
    if not nombre:
        return ""
    nombre = str(nombre).replace("\\", "/").rsplit("/", 1)[-1].strip()
    nombre = re.sub(r"[\x00-\x1f\x7f]", "", nombre)
    return nombre[:255]


def _nombre_original(archivo) -> str | None:
    return _limpiar_nombre(getattr(archivo, "filename", None)) or None


def _validar_componente(valor, nombre: str) -> str:
    """Valida un segmento de ruta que viene del cliente."""
    if not isinstance(valor, str) or not valor.strip():
        raise ErrorCargaArchivos(f"Falta el dato obligatorio '{nombre}'")
    valor = valor.strip()
    if (
        valor in (".", "..")
        or "\x00" in valor
        or any(caracter in valor for caracter in ("/", "\\", ":"))
        or os.path.basename(valor) != valor
    ):
        raise ErrorCargaArchivos(f"El dato '{nombre}' contiene una ruta inválida")
    return valor


def _abrir_stream(archivo):
    """Devuelve un stream legible sin importar el tipo recibido."""
    stream = getattr(archivo, "stream", None)
    if stream is None:
        if isinstance(archivo, (bytes, bytearray, memoryview)):
            return io.BytesIO(bytes(archivo))
        if hasattr(archivo, "read"):
            stream = archivo
        else:
            raise ErrorCargaArchivos("Se recibió un archivo con un formato no soportado")
    if hasattr(stream, "seek"):
        try:
            stream.seek(0)
        except (OSError, ValueError):
            pass
    return stream


def _extension(archivo, nombre_original: str | None) -> str:
    if nombre_original:
        extension = os.path.splitext(nombre_original)[1].lower()
        if _EXTENSION_VALIDA.match(extension):
            return extension

    mimetype = (
        getattr(archivo, "mimetype", None)
        or getattr(archivo, "content_type", None)
        or ""
    )
    if mimetype:
        extension = (
            mimetypes.guess_extension(mimetype.split(";")[0].strip()) or ""
        ).lower()
        if extension == ".jpe":
            extension = ".jpg"
        if _EXTENSION_VALIDA.match(extension):
            return extension
    return ".bin"


def _guardar(archivo, destino: str) -> None:
    """Copia el stream a disco por bloques (no usa read() completo)."""
    try:
        with open(destino, "wb") as salida:
            shutil.copyfileobj(_abrir_stream(archivo), salida, length=_BUFFER_ESCRITURA)
    except ErrorCargaArchivos:
        raise
    except Exception as exc:
        raise ErrorCargaArchivos(
            f"No se pudo guardar '{os.path.basename(destino)}': {exc}", 500
        ) from exc


def _validar_nombre_archivo(nombre: str, etiqueta: str) -> str:
    """Valida que el nombre venga suelto (sin rutas) y lo devuelve tal cual."""
    if not isinstance(nombre, str) or not nombre.strip():
        raise ErrorCargaArchivos(f"{etiqueta} contiene un archivo sin nombre")

    limpio = _limpiar_nombre(nombre)
    if (
        not limpio
        or limpio != nombre.strip()
        or any(caracter in nombre for caracter in ("/", "\\", ":"))
    ):
        raise ErrorCargaArchivos(f"{etiqueta} contiene un nombre inválido: '{nombre}'")

    return _validar_componente(limpio, "archivo")


def _exigir_extension_aceptada(nombre: str) -> None:
    if os.path.splitext(nombre)[1].lower() not in _EXTENSIONES_ACEPTADAS:
        raise ErrorCargaArchivos(
            "Solo se aceptan archivos .jpg, .jpeg, .png o .pdf"
        )


def _clave_orden(nombre: str):
    """Orden natural: ``0002`` antes que ``0010`` y que ``2``."""
    return [
        (0, int(parte)) if parte.isdigit() else (1, parte.lower())
        for parte in re.split(r"(\d+)", nombre)
        if parte != ""
    ]


def _cargar_libro(archivo_zip, directorio: str) -> list[str]:
    """Extrae las imágenes/PDF del ZIP y devuelve la lista de nombres."""
    try:
        zf = zipfile.ZipFile(_abrir_stream(archivo_zip))
    except zipfile.BadZipFile as exc:
        raise ErrorCargaArchivos("El archivo enviado no es un ZIP válido") from exc

    with zf:
        entradas = []
        vistos: set[str] = set()
        vistos_casefold: set[str] = set()

        for info in zf.infolist():
            if info.is_dir():
                continue

            nombre = _validar_nombre_archivo(info.filename, "El ZIP")
            if os.path.splitext(nombre)[1].lower() not in _EXTENSIONES_ACEPTADAS:
                continue

            if nombre in vistos:
                raise ErrorCargaArchivos(
                    f"El ZIP contiene más de una entrada llamada '{nombre}'"
                )
            clave = nombre.casefold()
            if clave in vistos_casefold:
                raise ErrorCargaArchivos(
                    f"El ZIP contiene nombres que solo difieren en mayúsculas: "
                    f"'{nombre}'"
                )
            vistos.add(nombre)
            vistos_casefold.add(clave)
            entradas.append((nombre, info))

        if not entradas:
            raise ErrorCargaArchivos(
                "El ZIP no contiene archivos .jpg, .jpeg, .png o .pdf en la raíz"
            )

        entradas.sort(key=lambda par: _clave_orden(par[0]))

        content = []
        for nombre, info in entradas:
            destino = os.path.join(directorio, nombre)
            try:
                with zf.open(info) as origen, open(destino, "wb") as salida:
                    shutil.copyfileobj(origen, salida, length=_BUFFER_ESCRITURA)
            except ErrorCargaArchivos:
                raise
            except Exception as exc:
                raise ErrorCargaArchivos(
                    f"No se pudo extraer '{nombre}': {exc}", 500
                ) from exc
            content.append(nombre)

    return content


def _cargar_archivo_suelto(archivo, directorio: str) -> list[str]:
    """Guarda el único archivo del item y devuelve su nombre normalizado."""
    nombre_original = _validar_nombre_archivo(
        _nombre_original(archivo) or "", "El envío"
    )
    _exigir_extension_aceptada(nombre_original)

    base, extension = os.path.splitext(nombre_original)
    nombre = f"{normalizar_setspec(base) or 'archivo'}{extension.lower()}"
    _guardar(archivo, os.path.join(directorio, nombre))
    return [nombre]


def _ruta_zip_subido(upload_id: str) -> str:
    """Valida el ``upload_id`` y devuelve la ruta del ZIP temporal."""
    if not isinstance(upload_id, str) or not re.fullmatch(r"[0-9a-f]{32}", upload_id):
        raise ErrorCargaArchivos("'zip_upload_id' no es válido")

    raiz = os.getenv("FILES_ROOT")
    if not raiz:
        raise ErrorCargaArchivos("FILES_ROOT no está configurado", 500)

    ruta = os.path.join(os.path.abspath(raiz), "tmp", f"{upload_id}.zip")
    if not os.path.isfile(ruta):
        raise ErrorCargaArchivos(
            "El archivo subido no existe o ya fue procesado", 404
        )
    return ruta


def eliminar_zip_subido(upload_id: str) -> bool:
    """Borra el ZIP temporal después de que el item quedó insertado en Mongo.

    Devuelve ``True`` si lo borró y ``False`` si ya no existía. Lanza
    ``ErrorCargaArchivos`` si el id es inválido o si el borrado falla.
    """
    ruta = _ruta_zip_subido(upload_id)
    try:
        os.remove(ruta)
        return True
    except FileNotFoundError:
        return False
    except OSError as exc:
        raise ErrorCargaArchivos(
            f"No se pudo borrar el ZIP temporal: {exc}", 500
        ) from exc


def _normalizar_files(files) -> list:
    if files is None:
        return []
    if hasattr(files, "read") or hasattr(files, "stream") or isinstance(
        files, (str, bytes, bytearray, memoryview)
    ):
        return [files]
    if isinstance(files, list):
        return files
    return list(files)


def cargar_archivos_pendiente(
    origen: str,
    ruta: dict,
    files: list,
    libro: bool = False,
    zip_upload_id: str | None = None,
) -> list:
    """Deja los archivos en ``FILES_ROOT/pendiente/...`` y devuelve ``content``.

    Lanza ``ErrorCargaArchivos`` con ``status`` 400/500 ante datos inválidos o
    fallos de disco. No deja archivos a medias: todo se escribe primero en un
    directorio temporal y se renombra al final.
    """
    files = _normalizar_files(files)

    if isinstance(libro, str):
        libro = libro.strip().lower() in {"1", "true", "si", "sí", "yes"}

    if not files and not (libro and zip_upload_id):
        raise ErrorCargaArchivos("No se recibió ningún archivo para el item")

    if not isinstance(ruta, dict):
        raise ErrorCargaArchivos("'ruta' debe ser un objeto")

    raiz = os.getenv("FILES_ROOT")
    if not raiz:
        raise ErrorCargaArchivos("FILES_ROOT no está configurado", 500)

    coleccion = _validar_componente(ruta.get("coleccion"), "coleccion")
    subcoleccion = _validar_componente(ruta.get("subcoleccion"), "subcoleccion")
    internal_id = _validar_componente(ruta.get("internal_id"), "internal_id")

    raiz_abs = os.path.abspath(raiz)
    base = os.path.join(raiz_abs, "pendiente", coleccion, subcoleccion)
    destino_final = os.path.join(base, internal_id)

    if os.path.exists(destino_final):
        raise ErrorCargaArchivos(
            f"Ya existe una carga pendiente en '{coleccion}/{subcoleccion}/{internal_id}'"
        )

    fuente_libro = None
    ruta_zip_temporal = None

    if libro:
        if zip_upload_id:
            ruta_zip_temporal = _ruta_zip_subido(zip_upload_id)
            try:
                fuente_libro = open(ruta_zip_temporal, "rb")
            except OSError as exc:
                raise ErrorCargaArchivos(
                    f"No se pudo abrir el ZIP subido: {exc}", 500
                ) from exc
        elif len(files) == 1:
            if _extension(files[0], _nombre_original(files[0])) != ".zip":
                raise ErrorCargaArchivos("Para un libro el archivo debe ser un .zip")
            fuente_libro = files[0]
        elif not files:
            raise ErrorCargaArchivos(
                "Para un libro envía un .zip en 'files' o un 'zip_upload_id'"
            )
        else:
            raise ErrorCargaArchivos(
                "Para un libro se debe enviar un único archivo .zip"
            )
    elif len(files) != 1:
        raise ErrorCargaArchivos(
            "Un item que no es libro debe enviar exactamente un archivo"
        )

    try:
        os.makedirs(base, exist_ok=True)
        directorio_temporal = os.path.join(
            base, f".{internal_id}-{uuid.uuid4().hex}"
        )
        os.makedirs(directorio_temporal, exist_ok=False)
    except OSError as exc:
        raise ErrorCargaArchivos(
            f"No se pudo preparar el directorio pendiente: {exc}", 500
        ) from exc

    final_creado = False
    try:
        if libro:
            content = _cargar_libro(fuente_libro, directorio_temporal)
        else:
            content = _cargar_archivo_suelto(files[0], directorio_temporal)

        try:
            os.makedirs(destino_final, exist_ok=False)
            final_creado = True
        except FileExistsError as exc:
            raise ErrorCargaArchivos(
                f"Ya existe una carga pendiente en "
                f"'{coleccion}/{subcoleccion}/{internal_id}'"
            ) from exc
        except OSError as exc:
            raise ErrorCargaArchivos(
                f"No se pudo crear el directorio pendiente: {exc}", 500
            ) from exc

        # Se mueve archivo por archivo: el renombrado de directorios no siempre
        # está permitido (por ejemplo, bajo el sandbox de Windows).
        for entrada in os.scandir(directorio_temporal):
            os.replace(entrada.path, os.path.join(destino_final, entrada.name))
        shutil.rmtree(directorio_temporal, ignore_errors=True)
    except Exception:
        shutil.rmtree(directorio_temporal, ignore_errors=True)
        if final_creado:
            shutil.rmtree(destino_final, ignore_errors=True)
        raise
    finally:
        if fuente_libro is not None and hasattr(fuente_libro, "close"):
            try:
                fuente_libro.close()
            except OSError:
                pass

    logger.info(
        "Carga pendiente lista: origen=%s ruta=%s/%s/%s libro=%s archivos=%s",
        origen,
        coleccion,
        subcoleccion,
        internal_id,
        libro,
        len(content),
    )
    return content
