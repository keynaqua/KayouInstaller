from __future__ import annotations

import shutil
import zipfile
from pathlib import Path

from config import DATAPACKS_DIR_NAME, SHORT_HTTP_RETRIES, SHORT_HTTP_TIMEOUT
from logger import info, success
from packs import Pack, parse_pack_manifest, sync_packs
from utils.files import FileProgressCallback, replace_file, safe_relative_path
from utils.http import DownloadError, get_json
from utils.progress import ProgressCallback, RangedProgress

DATAPACK_PROGRESS_START = 90
DATAPACK_PROGRESS_END = 94
Datapack = Pack


def load_datapack_manifest(manifest_url: str, cache_version: str = "") -> list[Datapack]:
    try:
        data = get_json(manifest_url, timeout=SHORT_HTTP_TIMEOUT, retries=SHORT_HTTP_RETRIES, cache_key=cache_version)
    except DownloadError as exc:
        info(f"Datapacks ignorés : {exc}")
        return []
    return parse_pack_manifest(
        data,
        "datapacks.json",
        True,
        ("packs", "datapacks"),
    )


def update_datapacks(
    game_dir: str | Path,
    modpack_key: str,
    progress_callback: ProgressCallback | None = None,
    download_callback: FileProgressCallback | None = None,
    manifest: list[Datapack] | None = None,
) -> list[str]:
    game_path = Path(game_dir)
    packs = manifest if manifest is not None else load_datapack_manifest(modpack_key)
    if not packs:
        RangedProgress(progress_callback, DATAPACK_PROGRESS_START, DATAPACK_PROGRESS_END, 0).finish()
        return []
    info("Synchronisation des datapacks...")
    files = sync_packs(
        game_path / DATAPACKS_DIR_NAME,
        packs,
        info,
        progress_callback,
        download_callback,
        DATAPACK_PROGRESS_START,
        DATAPACK_PROGRESS_END,
    )
    available = set(files)
    for pack in packs:
        if pack.file_name not in available:
            continue
        path = game_path / DATAPACKS_DIR_NAME / pack.file_name
        try:
            with zipfile.ZipFile(path) as archive:
                if "pack.mcmeta" not in archive.namelist():
                    raise RuntimeError(f"pack.mcmeta absent: {pack.file_name}")
        except zipfile.BadZipFile as exc:
            raise RuntimeError(f"Datapack invalide: {pack.file_name}") from exc
    success("Datapacks synchronises avec succes !")
    return files


def deploy_datapacks(game_dir: str | Path, packs: list[Datapack], worlds: list[str]) -> list[str]:
    game_path = Path(game_dir)
    deployed = []
    for world in worlds:
        relative = safe_relative_path(world, "monde")
        if len(relative.parts) != 1:
            raise RuntimeError(f"Monde invalide: {world}")
        world_dir = game_path / "saves" / relative
        if not world_dir.is_dir():
            raise RuntimeError(f"Monde introuvable: {world}")
        target_dir = world_dir / DATAPACKS_DIR_NAME
        target_dir.mkdir(parents=True, exist_ok=True)
        for pack in packs:
            target = target_dir / pack.file_name
            if pack.active:
                stage = target.with_suffix(target.suffix + ".tmp")
                shutil.copy2(game_path / DATAPACKS_DIR_NAME / pack.file_name, stage)
                replace_file(stage, target)
                deployed.append((Path("saves") / relative / DATAPACKS_DIR_NAME / pack.file_name).as_posix())
            else:
                target.unlink(missing_ok=True)
    return deployed
