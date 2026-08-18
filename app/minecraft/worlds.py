import gzip
import shutil
import struct
from pathlib import Path

from utils.resources import resource_path


def _replace_level_name(data: bytes, name: str) -> bytes:
    marker = b"\x08\x00\x09LevelName"
    index = data.find(marker)
    if index < 0:
        raise RuntimeError("Le template de monde ne contient pas LevelName.")
    length_at = index + len(marker)
    old_length = struct.unpack(">H", data[length_at:length_at + 2])[0]
    value_at = length_at + 2
    encoded = name.encode("utf-8")
    return data[:length_at] + struct.pack(">H", len(encoded)) + encoded + data[value_at + old_length:]


def _replace_numeric(data: bytes, tag_type: int, name: str, value: int) -> bytes:
    marker = bytes((tag_type,)) + struct.pack(">H", len(name)) + name.encode("utf-8")
    index = data.find(marker)
    if index < 0:
        raise RuntimeError(f"Le template de monde ne contient pas {name}.")
    value_at = index + len(marker)
    if tag_type == 1:
        return data[:value_at] + struct.pack(">b", value) + data[value_at + 1:]
    if tag_type == 3:
        return data[:value_at] + struct.pack(">i", value) + data[value_at + 4:]
    raise RuntimeError(f"Type NBT non supporté pour {name}.")


def create_world(
    game_dir: Path,
    folder: str,
    display_name: str,
    minecraft_version: str,
    game_mode: int = 0,
    difficulty: int = 2,
    allow_commands: bool = False,
) -> Path:
    template = resource_path(f"assets/world_templates/{minecraft_version}/level.dat")
    try:
        payload = gzip.decompress(template.read_bytes())
    except (OSError, EOFError) as exc:
        raise RuntimeError(f"Template de monde {minecraft_version} absent ou invalide.") from exc
    if len(payload) < 1000 or b"WorldGenSettings" not in payload:
        raise RuntimeError(f"Template de monde {minecraft_version} incomplet.")
    world_dir = game_dir / "saves" / folder
    (world_dir / "datapacks").mkdir(parents=True, exist_ok=True)
    level_dat = world_dir / "level.dat"
    payload = _replace_level_name(payload, display_name)
    payload = _replace_numeric(payload, 3, "GameType", game_mode)
    payload = _replace_numeric(payload, 1, "Difficulty", difficulty)
    payload = _replace_numeric(payload, 1, "allowCommands", int(allow_commands))
    with gzip.open(level_dat, "wb") as output:
        output.write(payload)
    default_icon = resource_path("assets/world_templates/default_icon.png")
    if default_icon.is_file():
        shutil.copy2(default_icon, world_dir / "icon.png")
    check = gzip.decompress(level_dat.read_bytes())
    if b"WorldGenSettings" not in check or display_name.encode("utf-8") not in check:
        raise RuntimeError(f"Le monde '{display_name}' n'a pas pu être validé.")
    return world_dir
