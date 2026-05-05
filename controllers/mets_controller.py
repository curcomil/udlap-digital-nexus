"""
METS AIP Generator - DSpace format
Genera AIPs en formato METS compatibles con la migración a Alma Specto.

Estructura de salida:
    output/
    └── {setspec}/
        ├── COMMUNITY@9999-{id}.zip
        ├── COLLECTION@9999-{id}.zip
        └── ITEM@9999-{internal_id}.zip
"""

import io
import os
import tarfile
import traceback as tb
from datetime import datetime
from pathlib import Path

from utils.mets_downloader import download_with_reporting
from utils.mets_ids import HANDLE_PREFIX, assign_handle_ids, make_zip_name, slugify_id
from utils.mets_packager import pack_container_zip, pack_item_zip
from utils.mets_report import write_report
from utils.mets_xml import build_collection_mets, build_community_mets

OUTPUT_DIR = Path(r"C:/Users/26193/Desktop/Mets")


def create_mets(
    items: list[dict], col_structure: dict, col_name: str, set_spec: str
) -> dict:
    """
    Orquesta la generación completa del tar.gz para una colección.

    Args:
        items:         lista de documentos MongoDB (los items del acervo)
        col_structure: documento MongoDB de la colección (con subcolecciones)
        col_name:      nombre legible de la colección
        set_spec:      setspec usado como nombre de carpeta/archivo de salida
    """
    clean_set_spec = set_spec.replace(":", "_")
    out_dir = os.path.join(OUTPUT_DIR, clean_set_spec)
    os.makedirs(out_dir, exist_ok=True)
    tar_path = os.path.join(out_dir, f"{clean_set_spec}.tar.gz")
    report_path = os.path.join(out_dir, f"{clean_set_spec}_informe.txt")

    report_issues: list[dict] = []

    def _add_issue(
        level: str,
        zip_name: str,
        internal_id: str,
        titulo: str,
        file_name: str,
        url: str,
        detail: str,
    ) -> None:
        report_issues.append(
            {
                "level": level,
                "zip": zip_name,
                "internal_id": internal_id,
                "titulo": titulo,
                "file_name": file_name,
                "url": url,
                "detail": detail,
            }
        )

    community_id, sub_ids = assign_handle_ids(col_structure)

    items_by_sub: dict[str, list] = {}
    for item in items:
        sub = item.get("subcoleccion", "__sin_subcoleccion__")
        items_by_sub.setdefault(sub, []).append(item)

    total_items = len(items)
    processed = 0
    item_errors = 0
    started_at = datetime.now()

    print(f"\n{'='*60}")
    print(f"  Generando METS AIP para: {col_name}")
    print(f"  Items totales : {total_items}")
    print(f"  Salida        : {tar_path}")
    print(f"  Informe       : {report_path}")
    print(f"{'='*60}")

    all_col_handle_ids: list[str] = []
    sub_item_map: dict[str, list[str]] = {}
    zip_buffer: list[tuple[str, bytes]] = []

    for sub_name, sub_items in items_by_sub.items():
        sub_spec = slugify_id(sub_name)
        col_id = sub_ids.get(sub_spec, sub_spec)
        all_col_handle_ids.append(f"{HANDLE_PREFIX}/{col_id}")
        sub_item_map[col_id] = []

        print(f"\n  📁 Subcolección: {sub_name} ({len(sub_items)} items)")

        for idx, record in enumerate(sub_items, start=1):
            internal_id = record.get("internal_id", f"item_{idx}")
            titulo = record.get("metadata", {}).get("titulo", "Sin título")
            zip_name = make_zip_name("ITEM", internal_id)

            print(
                f"    [{processed+1:>4}/{total_items}] {titulo[:55]}...",
                end=" ",
                flush=True,
            )

            try:
                if "content" in record:
                    all_pages = [
                        page
                        for section in record["content"]
                        for page in section.get("pages", [])
                    ]
                else:
                    url = record.get("url", "")
                    file_name = record.get("metadata", {}).get("imagen") or (
                        url.rstrip("/").split("/")[-1] if url else "imagen.jpg"
                    )
                    all_pages = [{"file_name": file_name, "url": url, "number": 1}]

                file_data = download_with_reporting(
                    all_pages, zip_name, internal_id, titulo, _add_issue
                )

                missing = sum(1 for d, _, _ in file_data.values() if d is None)

                item_zip = pack_item_zip(record, internal_id, col_id, file_data)
                zip_buffer.append((zip_name, item_zip))
                sub_item_map[col_id].append(f"{HANDLE_PREFIX}/{internal_id}")

                processed += 1
                status = f"✓ ({len(all_pages)} imgs"
                if missing:
                    status += f", ⚠ {missing} faltantes"
                print(status + ")")

            except Exception as e:
                detail = f"{type(e).__name__}: {e}\n{tb.format_exc()}"
                _add_issue("ITEM", zip_name, internal_id, titulo, "", "", detail)
                item_errors += 1
                processed += 1
                print(f"✗ ERROR CRÍTICO: {e}")

        col_mets = build_collection_mets(
            sub_name, col_id, community_id, sub_item_map[col_id]
        )
        col_zip = pack_container_zip(col_mets)
        zip_buffer.append((make_zip_name("COLLECTION", col_id), col_zip))
        print(f"    ✓ COLLECTION AIP ({len(sub_item_map[col_id])} items)")

    com_mets = build_community_mets(col_name, community_id, all_col_handle_ids)
    com_zip = pack_container_zip(com_mets)
    zip_buffer.append((make_zip_name("COMMUNITY", community_id), com_zip))
    print(f"\n  ✓ COMMUNITY AIP generado")

    print(f"\n  📦 Empaquetando tar.gz...", end=" ", flush=True)
    with tarfile.open(tar_path, "w:gz") as tar:
        for zname, zbytes in zip_buffer:
            info = tarfile.TarInfo(name=zname)
            info.size = len(zbytes)
            tar.addfile(info, io.BytesIO(zbytes))
    print("✓")

    write_report(
        report_path,
        col_name,
        set_spec,
        started_at,
        total_items,
        processed,
        item_errors,
        report_issues,
    )

    tar_mb = os.path.getsize(tar_path) / (1024 * 1024)
    file_issues = sum(1 for i in report_issues if i["level"] == "FILE")
    print(f"\n{'='*60}")
    print(f"  ✅ Items procesados : {processed - item_errors}/{total_items}")
    if item_errors:
        print(f"  ❌ Items con error  : {item_errors}")
    if file_issues:
        print(f"  ⚠  Archivos faltantes: {file_issues}")
    print(f"  📄 tar.gz  : {tar_path} ({tar_mb:.1f} MB)")
    print(f"  📋 Informe : {report_path}")
    print(f"{'='*60}\n")

    return {
        "status": "ok",
        "items_processed": processed - item_errors,
        "items_errors": item_errors,
        "files_missing": file_issues,
        "output": tar_path,
        "report": report_path,
    }
