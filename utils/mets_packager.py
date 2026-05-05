import io
import zipfile

from .mets_xml import build_item_mets


def pack_item_zip(
    record: dict, item_handle_id: str, collection_handle_id: str, file_data: dict
) -> bytes:
    mets_xml = build_item_mets(record, item_handle_id, collection_handle_id, file_data)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("mets.xml", mets_xml)
        for fn, (data, _, _) in file_data.items():
            if data:
                zf.writestr(fn, data)
    return buf.getvalue()


def pack_container_zip(mets_xml: bytes) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("mets.xml", mets_xml)
    return buf.getvalue()
