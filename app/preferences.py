import json
import os
from pathlib import Path

from config import CACHE_DIR_NAME
from utils.files import atomic_write_text


def _path() -> Path:
    root = Path(os.getenv("LOCALAPPDATA") or Path.cwd()) / CACHE_DIR_NAME
    return root / "settings.json"


def load_preferences() -> dict:
    try:
        data = json.loads(_path().read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def save_preferences(data: dict) -> None:
    atomic_write_text(_path(), json.dumps(data, indent=2, ensure_ascii=False) + "\n")
