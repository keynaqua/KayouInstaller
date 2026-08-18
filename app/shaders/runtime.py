from __future__ import annotations

from pathlib import Path

from config import (
    SHADERPACKS_DIR_NAME,
    SHORT_HTTP_RETRIES,
    SHORT_HTTP_TIMEOUT,
)
from logger import shader, success
from packs import Pack, parse_pack_manifest, sync_packs
from utils.files import FileProgressCallback, atomic_write_text
from utils.http import DownloadError, get_json
from utils.progress import ProgressCallback, RangedProgress

SHADERPACK_PROGRESS_START = 80
SHADERPACK_PROGRESS_END = 90


ShaderPack = Pack


def load_shaderpack_manifest(manifest_url: str, cache_version: str = "") -> list[ShaderPack]:
    try:
        data = get_json(
            manifest_url,
            timeout=SHORT_HTTP_TIMEOUT,
            retries=SHORT_HTTP_RETRIES,
            cache_key=cache_version,
        )
    except DownloadError as exc:
        shader(f"Shaderpacks ignorés : {exc}")
        return []

    return parse_pack_manifest(
        data,
        "shaderpacks.json",
        False,
        ("packs", "shaders"),
        True,
    )


def activate_shader(game_dir: Path, packs: list[ShaderPack], enabled: bool = True, preferred: str = "") -> None:
    path = game_dir / "config" / "iris.properties"
    lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    active = next(
        (pack.file_name for pack in packs if enabled and pack.active and (game_dir / SHADERPACKS_DIR_NAME / pack.file_name).is_file()),
        "",
    )
    if enabled and preferred:
        active = preferred
    if active:
        base = active.removesuffix(".zip")
        generated = next(
            (
                pack.file_name.removesuffix(".txt")
                for pack in packs
                if pack.file_name.endswith(".txt")
                and pack.file_name.startswith(f"{base} + EuphoriaPatches_")
            ),
            "",
        )
        if generated:
            active = generated
    values = {"enableShaders": str(bool(active)).lower(), "shaderPack": active}
    output = []
    found = set()
    for line in lines:
        key = line.split("=", 1)[0]
        if key in values:
            output.append(f"{key}={values[key]}")
            found.add(key)
        else:
            output.append(line)
    output.extend(f"{key}={value}" for key, value in values.items() if key not in found)
    atomic_write_text(path, "\n".join(output) + "\n")


def ensure_shaders_installed(
    game_dir: str | Path,
    modpack_key: str,
    progress_callback: ProgressCallback | None = None,
    download_callback: FileProgressCallback | None = None,
    manifest: list[ShaderPack] | None = None,
) -> list[str]:
    game_path = Path(game_dir)
    shaderpacks_dir = game_path / SHADERPACKS_DIR_NAME

    shader("Chargement du manifest shaderpacks...")
    packs = manifest if manifest is not None else load_shaderpack_manifest(modpack_key)
    if not packs:
        RangedProgress(progress_callback, SHADERPACK_PROGRESS_START, SHADERPACK_PROGRESS_END, 0).finish()
        success("Configuration des shaderpacks terminee !")
        return []

    sync_packs(
        shaderpacks_dir,
        packs,
        shader,
        progress_callback,
        download_callback,
        SHADERPACK_PROGRESS_START,
        SHADERPACK_PROGRESS_END,
    )
    success("Configuration des shaderpacks terminee !")
    return [pack.file_name for pack in packs]
