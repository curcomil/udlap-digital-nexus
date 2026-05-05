import hashlib
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

DOWNLOAD_WORKERS = 8
REQUEST_TIMEOUT = 30
DOWNLOAD_RETRY = 2
DOWNLOAD_DELAY = 0.3


def download_file(url: str) -> tuple[bytes, str, int]:
    if not url or not url.strip():
        raise ValueError("URL vacía o nula")

    last_exc = None
    for attempt in range(1 + DOWNLOAD_RETRY):
        try:
            resp = requests.get(url, timeout=REQUEST_TIMEOUT, verify=False)
            resp.raise_for_status()
            data = resp.content
            md5 = hashlib.md5(data).hexdigest()
            return data, md5, len(data)
        except Exception as e:
            last_exc = e
            if attempt < DOWNLOAD_RETRY:
                time.sleep(DOWNLOAD_DELAY * (attempt + 1))

    raise last_exc


def download_all_pages(pages: list[dict]) -> dict[str, tuple[bytes, str, int]]:
    results = {}
    with ThreadPoolExecutor(max_workers=DOWNLOAD_WORKERS) as executor:
        future_to_page = {}
        for page in pages:
            url = page.get("url", "")
            if not url or not url.strip():
                results[page["file_name"]] = (None, "", 0)
                continue
            time.sleep(DOWNLOAD_DELAY)
            future_to_page[executor.submit(download_file, url)] = page

        for future in as_completed(future_to_page):
            page = future_to_page[future]
            try:
                data, md5, size = future.result()
                results[page["file_name"]] = (data, md5, size)
            except Exception as e:
                print(f"    ⚠ Error descargando {page['file_name']}: {e}")
                results[page["file_name"]] = (None, "", 0)
    return results


def download_with_reporting(
    pages: list[dict], zip_name: str, internal_id: str, titulo: str, add_issue
) -> dict:
    results = {}
    with ThreadPoolExecutor(max_workers=DOWNLOAD_WORKERS) as executor:
        future_to_page = {}
        for page in pages:
            url = page.get("url", "")
            if not url or not url.strip():
                results[page["file_name"]] = (None, "", 0)
                add_issue(
                    "FILE",
                    zip_name,
                    internal_id,
                    titulo,
                    page["file_name"],
                    url or "(vacía)",
                    "URL ausente o vacía en el documento MongoDB",
                )
                continue
            time.sleep(DOWNLOAD_DELAY)
            future_to_page[executor.submit(download_file, url)] = page

        for future in as_completed(future_to_page):
            page = future_to_page[future]
            try:
                data, md5, size = future.result()
                results[page["file_name"]] = (data, md5, size)
            except Exception as e:
                results[page["file_name"]] = (None, "", 0)
                add_issue(
                    "FILE",
                    zip_name,
                    internal_id,
                    titulo,
                    page["file_name"],
                    page.get("url", ""),
                    f"{type(e).__name__}: {e}",
                )

    return results
