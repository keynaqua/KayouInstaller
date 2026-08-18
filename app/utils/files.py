from __future__ import annotations

import hashlib
import os
import tempfile
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from config import DOWNLOAD_WORKERS, HASH_CHUNK_SIZE
from utils.http import DownloadError, download_file

FileProgressCallback = Callable[[str, int, int | None, float], None]


@dataclass(frozen=True)
class VerifiedDownload:
    url: str
    target: Path
    algorithm: str
    digest: str


def bind_progress(name: str, callback: FileProgressCallback | None):
    if callback is None:
        return None
    return lambda received, total, speed: callback(name, received, total, speed)


def file_hash(path: Path, algorithm: str) -> str:
    digest = hashlib.new(algorithm)
    with path.open("rb") as file:
        while chunk := file.read(HASH_CHUNK_SIZE):
            digest.update(chunk)
    return digest.hexdigest()


def validate_digest(value: str, algorithm: str, label: str) -> str:
    value = value.lower()
    size = hashlib.new(algorithm).digest_size * 2
    if len(value) != size or any(char not in "0123456789abcdef" for char in value):
        raise RuntimeError(f"{label}: hash {algorithm} invalide")
    return value


def safe_relative_path(value: str, label: str) -> Path:
    path = Path(value.replace("\\", "/"))
    if not value or not path.parts or path.drive or path.is_absolute() or ".." in path.parts:
        raise RuntimeError(f"{label}: chemin invalide")
    return path


def validate_url(value: str, label: str) -> str:
    if urlparse(value).scheme.lower() not in {"http", "https"}:
        raise RuntimeError(f"{label}: URL invalide")
    return value


def validate_format(data: dict, label: str) -> None:
    if data.get("format", 1) != 1:
        raise RuntimeError(f"{label}: format non supporte")


def atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, stage_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(handle, "w", encoding="utf-8", newline="") as file:
            file.write(content)
        replace_file(stage_name, path)
    except Exception:
        Path(stage_name).unlink(missing_ok=True)
        raise


def replace_file(source: str | Path, target: str | Path) -> None:
    for attempt in range(5):
        try:
            os.replace(source, target)
            return
        except PermissionError:
            if attempt == 4:
                raise
            time.sleep(0.05 * (attempt + 1))


def download_verified(
    url: str,
    target: Path,
    algorithm: str,
    digest: str,
    callback: FileProgressCallback | None = None,
) -> bool:
    if target.exists() and file_hash(target, algorithm) == digest:
        return False

    target.parent.mkdir(parents=True, exist_ok=True)
    handle, stage_name = tempfile.mkstemp(prefix=f".{target.name}.", suffix=".stage", dir=target.parent)
    os.close(handle)
    stage = Path(stage_name)
    stage.unlink()
    progress = bind_progress(target.name, callback)

    try:
        download_file(url, stage, callback=progress)
        if file_hash(stage, algorithm) != digest:
            raise RuntimeError(f"Hash {algorithm} invalide pour {target.name}")
        replace_file(stage, target)
        return True
    finally:
        stage.unlink(missing_ok=True)
        stage.with_suffix(stage.suffix + ".part").unlink(missing_ok=True)


def download_many(
    files: list[VerifiedDownload],
    callback: FileProgressCallback | None = None,
    complete: Callable[[VerifiedDownload], None] | None = None,
    skip_missing: bool = False,
    skip_errors: bool = False,
) -> list[VerifiedDownload]:
    if not files:
        return []
    missing = []
    with ThreadPoolExecutor(max_workers=min(DOWNLOAD_WORKERS, len(files))) as pool:
        pending = {
            pool.submit(
                download_verified,
                item.url,
                item.target,
                item.algorithm,
                item.digest,
                callback,
            ): item
            for item in files
        }
        for future in as_completed(pending):
            item = pending[future]
            try:
                future.result()
            except DownloadError as exc:
                if not skip_errors and (not skip_missing or "404" not in str(exc)):
                    raise
                missing.append(item)
                continue
            if complete:
                complete(item)
    return missing
