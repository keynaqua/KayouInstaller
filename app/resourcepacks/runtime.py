from __future__ import annotations

import ast
import json
import zipfile
from pathlib import Path

from config import RESOURCEPACKS_DIR_NAME, SHORT_HTTP_RETRIES, SHORT_HTTP_TIMEOUT
from logger import success, txtp
from packs import Pack, parse_pack_manifest, sync_packs
from utils.files import FileProgressCallback, atomic_write_text
from utils.http import DownloadError, get_json
from utils.progress import ProgressCallback

RESOURCEPACK_PROGRESS_START = 70
RESOURCEPACK_PROGRESS_END = 80
ResourcePack = Pack


def load_resourcepack_manifest(manifest_url: str, cache_version: str = "") -> list[ResourcePack]:
    try:
        data = get_json(manifest_url, timeout=SHORT_HTTP_TIMEOUT, retries=SHORT_HTTP_RETRIES, cache_key=cache_version)
    except DownloadError as exc:
        txtp(f"Packs de ressources ignorés : {exc}")
        return []
    return parse_pack_manifest(
        data,
        "resourcepacks.json",
        True,
    )


def _quote(file_name: str) -> str:
    return f"file/{file_name}"


def _parse(value: str) -> list[str]:
    try:
        parsed = ast.literal_eval(value)
    except (SyntaxError, ValueError):
        return []
    return [item for item in parsed if isinstance(item, str)] if isinstance(parsed, list) else []


def _supports_format(value: object, expected: int) -> bool:
    if isinstance(value, int) and not isinstance(value, bool):
        return value == expected
    if isinstance(value, list) and len(value) == 2 and all(isinstance(item, int) for item in value):
        return min(value) <= expected <= max(value)
    if isinstance(value, dict):
        minimum = value.get("min_inclusive", value.get("min", expected))
        maximum = value.get("max_inclusive", value.get("max", expected))
        return isinstance(minimum, int) and isinstance(maximum, int) and minimum <= expected <= maximum
    return False


def _compatible(path: Path, expected_format: int) -> bool:
    try:
        with zipfile.ZipFile(path) as archive:
            data = json.loads(archive.read("pack.mcmeta").decode("utf-8-sig"))
        metadata = data.get("pack", {}) if isinstance(data, dict) else {}
        supported = metadata.get("supported_formats")
        value = supported if supported is not None else metadata.get("pack_format")
        return _supports_format(value, expected_format)
    except (OSError, KeyError, ValueError, zipfile.BadZipFile, UnicodeDecodeError):
        return False


def activate_resourcepacks(
    game_dir: Path,
    packs: list[ResourcePack],
    enabled: bool = True,
    expected_format: int = 34,
) -> None:
    path = game_dir / "options.txt"
    lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    managed = {_quote(pack.file_name) for pack in packs}
    selected = [pack for pack in packs if enabled and pack.active and (game_dir / RESOURCEPACKS_DIR_NAME / pack.file_name).is_file()]
    wanted = [_quote(pack.file_name) for pack in selected]
    incompatible = [
        _quote(pack.file_name)
        for pack in selected
        if not _compatible(game_dir / RESOURCEPACKS_DIR_NAME / pack.file_name, expected_format)
    ]
    output = []
    found = set()
    for line in lines:
        key, separator, value = line.partition(":")
        if not separator or key not in {"resourcePacks", "incompatibleResourcePacks"}:
            output.append(line)
            continue
        current = _parse(value)
        additions = wanted if key == "resourcePacks" else incompatible
        merged = [item for item in current if item not in managed] + additions
        output.append(f"{key}:{json.dumps(merged, ensure_ascii=False)}")
        found.add(key)
    for key in ("resourcePacks", "incompatibleResourcePacks"):
        if key not in found:
            additions = wanted if key == "resourcePacks" else incompatible
            output.append(f"{key}:{json.dumps(additions, ensure_ascii=False)}")
    atomic_write_text(path, "\n".join(output) + "\n")


def update_resourcepacks(
    game_dir: str | Path,
    modpack_key: str,
    progress_callback: ProgressCallback | None = None,
    download_callback: FileProgressCallback | None = None,
    manifest: list[ResourcePack] | None = None,
) -> list[str]:
    game_path = Path(game_dir)
    txtp("Chargement du manifest resourcepacks...")
    packs = manifest if manifest is not None else load_resourcepack_manifest(modpack_key)
    txtp("Synchronisation des resourcepacks...")
    sync_packs(
        game_path / RESOURCEPACKS_DIR_NAME,
        packs,
        txtp,
        progress_callback,
        download_callback,
        RESOURCEPACK_PROGRESS_START,
        RESOURCEPACK_PROGRESS_END,
    )
    success("Resourcepacks synchronises avec succes !")
    return [pack.file_name for pack in packs]
