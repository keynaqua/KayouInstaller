import base64
import json
from datetime import datetime, timezone
from pathlib import Path

from config import (
    DEFAULT_INSTALL_SUBDIRS,
    ICON,
    get_installation_dir,
    get_launcher_profiles_path,
)
from logger import success
from utils.files import atomic_write_text
from utils.http import get_bytes
from utils.system import build_java_args


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _ensure_installation_ready(name: str) -> Path:
    root = get_installation_dir(name)
    root.mkdir(parents=True, exist_ok=True)
    for subdir in DEFAULT_INSTALL_SUBDIRS:
        (root / subdir).mkdir(exist_ok=True)
    return root.resolve()


def _profile_icon(logo_url: str) -> str:
    try:
        if not logo_url:
            return ICON
        data = get_bytes(logo_url)
        return f"data:image/png;base64,{base64.b64encode(data).decode()}"
    except Exception:
        return ICON


def _create_launcher_profile(name: str, game_dir: Path, version_id: str, logo_url: str, ram_gb: int) -> None:
    launcher_file = get_launcher_profiles_path()
    data = json.loads(launcher_file.read_text(encoding="utf-8")) if launcher_file.exists() else {}
    profiles = data.setdefault("profiles", {})
    profile = profiles.setdefault(name, {"created": _now_iso()})

    profile.update(
        {
            "name": name,
            "type": "custom",
            "lastUsed": _now_iso(),
            "lastVersionId": version_id,
            "gameDir": str(game_dir),
            "icon": _profile_icon(logo_url),
        }
    )
    profile["javaArgs"] = build_java_args(ram_gb)
    atomic_write_text(launcher_file, json.dumps(data, indent=4, ensure_ascii=False))


def create_minecraft_profile(name: str, installation_dir: str, version_id: str, logo_url: str, ram_gb: int):
    """
    Prepare a dedicated Minecraft installation and keep its launcher
    profile aligned with the installed mod loader version.
    """
    install_path = get_installation_dir(installation_dir)
    already_exists = install_path.exists()

    path = _ensure_installation_ready(installation_dir)

    _create_launcher_profile(name, path, version_id, logo_url, ram_gb)

    if not already_exists:
        success("Installation de la config minecraft terminee")
    else:
        success("Installation deja presente, profil mis a jour")

    return path
