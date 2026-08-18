from __future__ import annotations

import json
import shutil
import stat
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from config import (
    INSTALLATIONS_DIR_NAME,
    DATAPACKS_DIR_NAME,
    MODS_DIR_NAME,
    RESOURCEPACKS_DIR_NAME,
    SHADERPACKS_DIR_NAME,
    get_installation_dir,
    get_launcher_profiles_path,
    get_minecraft_dir,
)
from logger import info, progress, success
from inventory import Inventory
from modpack import ModpackInfo, modpack_info_from_catalog
from utils.files import atomic_write_text


class UninstallMode(str, Enum):
    CLASSIC = "classic"
    FULL = "full"


@dataclass(frozen=True)
class ManifestFile:
    file_name: str


def _safe_child(base: Path, file_name: str) -> Path:
    target = (base / file_name).resolve()
    base_resolved = base.resolve()
    try:
        target.relative_to(base_resolved)
    except ValueError as exc:
        raise RuntimeError(f"Chemin manifest hors dossier autorise: {file_name}") from exc
    return target


def _remove_manifest_files(base: Path, files: list[ManifestFile], label: str) -> int:
    removed = 0
    if not base.exists():
        info(f"{label}: dossier absent, rien a supprimer.")
        return removed

    for item in files:
        target = _safe_child(base, item.file_name)
        if not target.exists():
            continue
        if target.is_dir():
            shutil.rmtree(target)
        else:
            target.unlink()
        removed += 1
        info(f"{label}: supprime {item.file_name}")

    success(f"{label}: {removed} fichier(s) supprime(s).")
    return removed


def _installation_path(modpack_info: ModpackInfo) -> Path:
    root = get_installation_dir(modpack_info.installation_dir).resolve()
    installations_root = (get_minecraft_dir() / INSTALLATIONS_DIR_NAME).resolve()
    try:
        root.relative_to(installations_root)
    except ValueError as exc:
        raise RuntimeError(f"Dossier d'installation invalide: {root}") from exc
    return root


def _remove_launcher_profile(profile_name: str) -> None:
    launcher_file = get_launcher_profiles_path()
    if not launcher_file.exists():
        return

    data = json.loads(launcher_file.read_text(encoding="utf-8"))
    profiles = data.get("profiles")
    if not isinstance(profiles, dict) or profile_name not in profiles:
        return

    del profiles[profile_name]
    atomic_write_text(launcher_file, json.dumps(data, indent=4, ensure_ascii=False))
    info(f"Profil launcher supprime: {profile_name}")


def _classic_uninstall(modpack_info: ModpackInfo) -> None:
    game_dir = _installation_path(modpack_info)
    if not game_dir.exists():
        info(f"Dossier absent: {game_dir}")
        return

    inventory = Inventory(game_dir, modpack_info.key)
    if inventory.path.exists():
        progress(45)
        categories = ("mods", "resourcepacks", "shaderpacks", "datapacks", "deployed_datapacks")
        files = [ManifestFile(path) for path in inventory.all_files(categories)]
        _remove_manifest_files(game_dir, files, "Fichiers du modpack")
        for category in categories:
            inventory.sync(category, [])
        inventory.set_installed(False)
        progress(100)
        success("Desinstallation classique terminee. Saves, options et configs conservees.")
        return

    progress(25)
    info("Inventaire absent : nettoyage local des dossiers gérés...")

    def local_files(directory: str) -> list[ManifestFile]:
        root = game_dir / directory
        return [ManifestFile(path.name) for path in root.iterdir()] if root.is_dir() else []

    mod_files = local_files(MODS_DIR_NAME)
    resourcepacks = local_files(RESOURCEPACKS_DIR_NAME)
    shaderpacks = local_files(SHADERPACKS_DIR_NAME)
    datapacks = local_files(DATAPACKS_DIR_NAME)

    progress(45)
    _remove_manifest_files(game_dir / MODS_DIR_NAME, mod_files, "Mods")

    progress(65)
    _remove_manifest_files(game_dir / RESOURCEPACKS_DIR_NAME, resourcepacks, "Resourcepacks")

    progress(85)
    _remove_manifest_files(game_dir / SHADERPACKS_DIR_NAME, shaderpacks, "Shaderpacks")

    progress(90)
    _remove_manifest_files(game_dir / DATAPACKS_DIR_NAME, datapacks, "Datapacks")

    inventory.set_installed(False)
    success("Desinstallation classique terminee. Saves, options et configs conservees.")


def _full_uninstall(modpack_info: ModpackInfo) -> None:
    game_dir = _installation_path(modpack_info)
    if game_dir.exists():
        override_config = game_dir / "config" / "resourcepackoverrides.json"
        if override_config.exists():
            override_config.chmod(stat.S_IREAD | stat.S_IWRITE)
        shutil.rmtree(game_dir)
        success(f"Dossier du modpack supprime: {game_dir}")
    else:
        info(f"Dossier deja absent: {game_dir}")

    _remove_launcher_profile(modpack_info.name)
    success("Desinstallation complete terminee.")


def uninstall_modpack(modpack, mode: UninstallMode | str) -> None:
    selected_mode = UninstallMode(mode)
    progress(5)
    info_data = modpack_info_from_catalog(modpack)

    progress(15)
    if selected_mode == UninstallMode.CLASSIC:
        _classic_uninstall(info_data)
    elif selected_mode == UninstallMode.FULL:
        _full_uninstall(info_data)

    progress(100)
