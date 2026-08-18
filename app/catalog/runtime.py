import json
import os
import time
from dataclasses import dataclass
from pathlib import Path

from config import CACHE_DIR_NAME, CATALOG_CACHE_FILE, CATALOG_CACHE_TTL, get_modpack_catalog_url
from utils.http import get_json
from utils.files import atomic_write_text, validate_format


@dataclass(frozen=True)
class CatalogEntry:
    id: str
    name: str
    description: str
    minecraft_version: str
    loader: str
    loader_version: str = "latest"
    installation_dir: str = ""
    java_version: int = 21
    recommended_ram_ratio: float = 0.65
    enabled: bool = True
    logo: str = ""
    loader_icon: str = ""
    size_mb: float | None = None
    revision: str = ""
    size_bytes: int | None = None
    base_url: str = ""
    manifests: dict[str, str] | None = None
    update_status: str = "Non installé"


def _required(entry: dict, field: str, index: int) -> str:
    value = entry.get(field)
    if not isinstance(value, str) or not value.strip():
        raise RuntimeError(f"catalog.json: modpacks[{index}].{field} invalide")
    return value.strip()


def _parse(data: object) -> list[CatalogEntry]:
    if not isinstance(data, dict) or not isinstance(data.get("modpacks"), list):
        raise RuntimeError("catalog.json doit contenir une liste 'modpacks'")
    validate_format(data, "catalog.json")

    packs = []
    ids = set()
    for index, entry in enumerate(data["modpacks"], start=1):
        if not isinstance(entry, dict):
            raise RuntimeError(f"catalog.json: modpacks[{index}] invalide")
        enabled = entry.get("enabled") is True
        pack = CatalogEntry(
            id=_required(entry, "id", index),
            name=_required(entry, "name", index),
            description=str(entry.get("description", "")).strip(),
            minecraft_version=_required(entry, "minecraft_version", index) if enabled else str(entry.get("minecraft_version", "")).strip(),
            loader=_required(entry, "loader", index).lower() if enabled else str(entry.get("loader", "")).strip().lower(),
            loader_version=str(entry.get("loader_version", "latest")).strip() or "latest",
            installation_dir=str(entry.get("installation_dir", entry.get("id", ""))).strip(),
            java_version=entry.get("java_version", 21) if isinstance(entry.get("java_version", 21), int) else 21,
            recommended_ram_ratio=float(entry.get("recommended_ram_ratio", 0.65))
            if isinstance(entry.get("recommended_ram_ratio", 0.65), (int, float))
            and not isinstance(entry.get("recommended_ram_ratio", 0.65), bool)
            else 0.65,
            enabled=enabled,
            logo=str(entry.get("logo", "")).strip(),
            loader_icon=str(entry.get("loader_icon", "")).strip(),
            size_mb=float(entry["size_mb"]) if isinstance(entry.get("size_mb"), (int, float)) and not isinstance(entry.get("size_mb"), bool) else None,
            revision=str(entry.get("revision", "")).strip(),
            size_bytes=entry.get("size_bytes") if isinstance(entry.get("size_bytes"), int) else None,
            base_url=str(entry.get("base_url", "")).strip(),
            manifests={
                str(key): str(value).strip()
                for key, value in entry.get("manifests", {}).items()
                if isinstance(key, str) and isinstance(value, str) and value.strip()
            } if isinstance(entry.get("manifests"), dict) else {},
        )
        if enabled and not pack.manifests:
            raise RuntimeError(f"catalog.json: modpacks[{index}].manifests invalide")
        if pack.id in ids:
            raise RuntimeError(f"catalog.json: id duplique '{pack.id}'")
        ids.add(pack.id)
        packs.append(pack)
    return packs


def _cache_path() -> Path | None:
    root = os.getenv("LOCALAPPDATA")
    return Path(root) / CACHE_DIR_NAME / CATALOG_CACHE_FILE if root else None


def _read_cache(path: Path, fresh_only: bool) -> object | None:
    try:
        if fresh_only and time.time() - path.stat().st_mtime > CATALOG_CACHE_TTL:
            return None
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _write_cache(path: Path | None, data: object) -> None:
    if not path:
        return
    atomic_write_text(path, json.dumps(data, ensure_ascii=False))


def load_catalog() -> list[CatalogEntry]:
    cache = _cache_path()
    if cache and (data := _read_cache(cache, True)) is not None:
        try:
            return _parse(data)
        except RuntimeError:
            # Une ancienne version de l'application peut avoir laissé un
            # catalogue GitHub incompatible : on le remplace immédiatement.
            pass
    try:
        data = get_json(get_modpack_catalog_url(), cache_ttl=0)
        packs = _parse(data)
        _write_cache(cache, data)
        return packs
    except Exception:
        if cache and (data := _read_cache(cache, False)) is not None:
            return _parse(data)
        raise
