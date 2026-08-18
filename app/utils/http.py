import json
import hashlib
import os
import time
from http.client import HTTPException
from collections.abc import Callable
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

from config import (
    HTTP_CHUNK_SIZE,
    HTTP_DOWNLOAD_RETRIES,
    HTTP_DOWNLOAD_RETRY_DELAY,
    HTTP_DOWNLOAD_TIMEOUT,
    DOWNLOAD_PROGRESS_INTERVAL,
    HTTP_JSON_RETRIES,
    HTTP_JSON_RETRY_DELAY,
    HTTP_JSON_TIMEOUT,
    PARTIAL_DOWNLOAD_SUFFIX,
    CACHE_DIR_NAME,
    HTTP_CACHE_DIR_NAME,
    HTTP_CACHE_TTL,
    HTTP_NEGATIVE_CACHE_TTL,
)

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0.0.0 Safari/537.36"
    ),
    "Accept": "*/*",
    "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
    "Connection": "close",
}


class DownloadError(RuntimeError):
    pass


DownloadCallback = Callable[[int, int | None, float], None]


def _cache_path(url: str, suffix: str, cache_key: str = "") -> Path:
    root = Path(os.getenv("LOCALAPPDATA") or Path.cwd()) / CACHE_DIR_NAME / HTTP_CACHE_DIR_NAME
    identity = f"{url}\n{cache_key}" if cache_key else url
    return root / f"{hashlib.sha256(identity.encode()).hexdigest()}{suffix}"


def _read_cache(url: str, suffix: str, fresh_only: bool, cache_key: str = "", ttl: int = HTTP_CACHE_TTL) -> bytes | None:
    path = _cache_path(url, suffix, cache_key)
    try:
        if fresh_only and time.time() - path.stat().st_mtime > ttl:
            return None
        return path.read_bytes()
    except OSError:
        return None


def _write_cache(url: str, suffix: str, data: bytes, cache_key: str = "") -> None:
    path = _cache_path(url, suffix, cache_key)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_bytes(data)
        temporary.replace(path)
    except OSError:
        pass


def _make_request(url: str, headers: dict | None = None) -> Request:
    merged_headers = dict(DEFAULT_HEADERS)
    if headers:
        merged_headers.update(headers)
    return Request(url, headers=merged_headers)


def get_json(
    url: str,
    timeout: int = HTTP_JSON_TIMEOUT,
    retries: int = HTTP_JSON_RETRIES,
    retry_delay: float = HTTP_JSON_RETRY_DELAY,
    cache_key: str = "",
    cache_ttl: int = HTTP_CACHE_TTL,
) -> dict | list:
    if cache_ttl > 0 and (cached := _read_cache(url, ".json", True, cache_key, cache_ttl)):
        try:
            return json.loads(cached.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            pass
    if _read_cache(url, ".missing", True, cache_key, HTTP_NEGATIVE_CACHE_TTL) is not None:
        raise DownloadError(f"Ressource JSON absente (cache): {url}")
    last_error = None
    attempts = max(1, retries)
    for attempt in range(1, attempts + 1):
        try:
            req = _make_request(url, {"Accept": "application/json"})
            with urlopen(req, timeout=timeout) as response:
                raw = response.read()
                encoding = response.headers.get_content_charset() or "utf-8"
                result = json.loads(raw.decode(encoding))
                _write_cache(url, ".json", json.dumps(result, ensure_ascii=False).encode("utf-8"), cache_key)
                return result

        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as e:
            last_error = e
            if attempt < attempts:
                time.sleep(retry_delay * attempt)
            else:
                break

    if cached := _read_cache(url, ".json", False, cache_key):
        try:
            return json.loads(cached.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            pass
    if isinstance(last_error, HTTPError) and last_error.code == 404:
        _write_cache(url, ".missing", b"missing", cache_key)
    raise DownloadError(f"Échec récupération JSON: {url} ({last_error})") from last_error


def get_text(
    url: str,
    timeout: int = HTTP_JSON_TIMEOUT,
    retries: int = HTTP_JSON_RETRIES,
    retry_delay: float = HTTP_JSON_RETRY_DELAY,
) -> str:
    last_error = None

    for attempt in range(1, retries + 1):
        try:
            with urlopen(_make_request(url), timeout=timeout) as response:
                raw = response.read()
                encoding = response.headers.get_content_charset() or "utf-8"
                return raw.decode(encoding)
        except (HTTPError, URLError, TimeoutError, OSError, UnicodeDecodeError) as e:
            last_error = e
            if attempt < retries:
                time.sleep(retry_delay * attempt)
            else:
                raise DownloadError(f"Echec recuperation texte: {url} ({e})") from e

    raise DownloadError(f"Echec recuperation texte: {url} ({last_error})")


def get_bytes(url: str, timeout: int = HTTP_JSON_TIMEOUT) -> bytes:
    if cached := _read_cache(url, ".bin", True):
        return cached
    last_error = None
    for request_url in [url]:
        try:
            with urlopen(_make_request(request_url), timeout=timeout) as response:
                data = response.read()
                _write_cache(url, ".bin", data)
                return data
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            last_error = exc
    if cached := _read_cache(url, ".bin", False):
        return cached
    raise DownloadError(f"Echec recuperation fichier: {url} ({last_error})") from last_error


def download_file(
    url: str,
    dest: Path,
    timeout: int = HTTP_DOWNLOAD_TIMEOUT,
    retries: int = HTTP_DOWNLOAD_RETRIES,
    retry_delay: float = HTTP_DOWNLOAD_RETRY_DELAY,
    chunk_size: int = HTTP_CHUNK_SIZE,
    callback: DownloadCallback | None = None,
) -> Path:
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)

    tmp_dest = dest.with_suffix(dest.suffix + PARTIAL_DOWNLOAD_SUFFIX)
    last_error = None

    for attempt in range(1, retries + 1):
        try:
            req = _make_request(url)

            with urlopen(req, timeout=timeout) as response:
                status = getattr(response, "status", None) or 200
                if status >= 400:
                    raise DownloadError(f"HTTP {status} sur {url}")

                total_header = response.headers.get("Content-Length")
                total = int(total_header) if total_header and total_header.isdigit() else None
                received = 0
                started = time.monotonic()
                last_report = started
                if callback:
                    callback(0, total, 0.0)
                with open(tmp_dest, "wb") as file:
                    while chunk := response.read(chunk_size):
                        file.write(chunk)
                        received += len(chunk)
                        now = time.monotonic()
                        if callback and (
                            now - last_report >= DOWNLOAD_PROGRESS_INTERVAL
                            or total is not None and received >= total
                        ):
                            callback(received, total, received / max(now - started, 0.001))
                            last_report = now
                if callback and (total is None or received < total):
                    callback(received, total, received / max(time.monotonic() - started, 0.001))
                if total is not None and received != total:
                    raise DownloadError(f"Telechargement incomplet: {received}/{total} octets")

            if not tmp_dest.exists() or tmp_dest.stat().st_size == 0:
                raise DownloadError(f"Fichier vide téléchargé depuis {url}")

            tmp_dest.replace(dest)
            return dest

        except (HTTPError, URLError, HTTPException, TimeoutError, OSError, DownloadError) as e:
            last_error = e

            if tmp_dest.exists():
                try:
                    tmp_dest.unlink()
                except OSError:
                    pass

            definitive_client_error = isinstance(e, HTTPError) and 400 <= e.code < 500 and e.code not in {408, 429}
            if definitive_client_error:
                raise DownloadError(
                    f"Échec téléchargement fichier: {url} -> {dest} ({e})"
                ) from e
            if attempt < retries:
                time.sleep(retry_delay * attempt)
            else:
                raise DownloadError(
                    f"Échec téléchargement fichier: {url} -> {dest} ({e})"
                ) from e

    raise DownloadError(f"Échec téléchargement fichier: {url} ({last_error})")
