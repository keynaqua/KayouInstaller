from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from config import INSTALLATIONS_DIR_NAME, INSTALLER_INVENTORY_FILE, INSTALLER_STATE_DIR_NAME, get_minecraft_dir
from utils.files import safe_relative_path
from utils.files import atomic_write_text


class Inventory:
    def __init__(self, game_dir: Path, modpack: str):
        self.game_dir = game_dir.resolve()
        self.path = self.game_dir / INSTALLER_STATE_DIR_NAME / INSTALLER_INVENTORY_FILE
        self.data = self._load()
        self.data["modpack"] = modpack

    def _load(self) -> dict:
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            if isinstance(data, dict) and isinstance(data.get("files"), dict):
                return data
        except (OSError, ValueError):
            pass
        return {"format": 1, "files": {}}

    def files(self, category: str) -> list[str]:
        values = self.data["files"].get(category, [])
        return [value for value in values if isinstance(value, str)]

    def has_category(self, category: str) -> bool:
        return category in self.data["files"]

    def sync(self, category: str, paths: list[str], remove_stale: bool = True) -> None:
        clean = sorted(set(paths))
        if remove_stale:
            for value in set(self.files(category)) - set(clean):
                target = self._target(value)
                if target.is_file():
                    target.unlink()
        self.data["files"][category] = clean
        self.save()

    def all_files(self, categories: tuple[str, ...] | None = None) -> list[str]:
        selected = categories or tuple(self.data["files"])
        return sorted({path for category in selected for path in self.files(category)})

    def save(self) -> None:
        self.data["updated_at"] = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        atomic_write_text(self.path, json.dumps(self.data, indent=2, ensure_ascii=False) + "\n")

    def set_installed(self, installed: bool) -> None:
        self.data["installed"] = installed
        self.save()

    def set_revision(self, revision: str) -> None:
        self.data["revision"] = revision
        self.save()

    def set_size_bytes(self, value: int) -> None:
        self.data["size_bytes"] = max(0, int(value))
        self.save()

    def _target(self, value: str) -> Path:
        target = (self.game_dir / safe_relative_path(value, "inventaire")).resolve()
        target.relative_to(self.game_dir)
        return target


def installed_modpacks() -> set[str]:
    try:
        root = get_minecraft_dir() / INSTALLATIONS_DIR_NAME
    except RuntimeError:
        return set()
    installed = set()
    for game_dir in root.iterdir() if root.is_dir() else ():
        if not game_dir.is_dir():
            continue
        path = game_dir / INSTALLER_STATE_DIR_NAME / INSTALLER_INVENTORY_FILE
        if not path.is_file():
            installed.add(game_dir.name.casefold())
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data.get("modpack"), str):
                installed.add(data["modpack"].casefold())
        except (OSError, ValueError):
            pass
    return installed


def classically_uninstalled_modpacks() -> set[str]:
    try:
        root = get_minecraft_dir() / INSTALLATIONS_DIR_NAME
    except RuntimeError:
        return set()
    modpacks = set()
    for path in root.glob(f"*/{INSTALLER_STATE_DIR_NAME}/{INSTALLER_INVENTORY_FILE}"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if data.get("installed") is False and isinstance(data.get("modpack"), str):
                modpacks.add(data["modpack"].casefold())
        except (OSError, ValueError):
            pass
    return modpacks


def installed_revisions() -> dict[str, str]:
    try:
        root = get_minecraft_dir() / INSTALLATIONS_DIR_NAME
    except RuntimeError:
        return {}
    revisions = {}
    for path in root.glob(f"*/{INSTALLER_STATE_DIR_NAME}/{INSTALLER_INVENTORY_FILE}"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data.get("modpack"), str):
                revisions[data["modpack"].casefold()] = str(data.get("revision", ""))
        except (OSError, ValueError):
            pass
    return revisions


def installed_sizes() -> dict[str, int]:
    try:
        root = get_minecraft_dir() / INSTALLATIONS_DIR_NAME
    except RuntimeError:
        return {}
    sizes = {}
    for path in root.glob(f"*/{INSTALLER_STATE_DIR_NAME}/{INSTALLER_INVENTORY_FILE}"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            key = data.get("modpack")
            size = data.get("size_bytes")
            if isinstance(key, str) and isinstance(size, int) and not isinstance(size, bool) and size >= 0:
                sizes[key.casefold()] = size
        except (OSError, ValueError):
            pass
    return sizes
