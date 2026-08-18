from __future__ import annotations

import ast
import json
import stat
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

MOD_PACK_IDS = (
    "mod/punchy:resourcepacks/punchy",
    "mod/item_interactions_mod:resourcepacks/example_gui_particles",
    "continuity:default",
    "fabric",
    "mod_resources",
    "eatinganimations_compat",
    "moonlight:merged_pack",
)


def _write_override_config(game_dir: Path, ordered: list[str]) -> None:
    # Resource Pack Overrides deliberately applies ``default_packs`` in
    # reverse (unlike options.txt).  Giving both files the same list makes a
    # recovery/reset invert the pack stack on the next Minecraft launch.
    defaults = list(reversed(ordered))
    overrides = {
        # Pack.Position uses the resource-pack screen terminology here. These
        # packs must remain movable, but new/recovered virtual packs must be
        # inserted at the bottom of the visible selection list.
        identifier: {"default_position": "BOTTOM", "fixed_position": False}
        for identifier in MOD_PACK_IDS
    }
    data = {
        # v21.1.0 serializes this value as a string. Match its own output so a
        # first launch does not treat our generated file as foreign config.
        "schema_version": "2",
        "failed_reloads_per_session": 5,
        "default_packs": defaults,
        "pack_overrides": overrides,
    }
    path = game_dir / "config" / "resourcepackoverrides.json"
    if path.exists():
        path.chmod(stat.S_IREAD | stat.S_IWRITE)
    # The mod's documentation explicitly requires section signs in pack ids
    # to remain JSON escaped (\\u00a7) in this file.
    atomic_write_text(path, json.dumps(data, indent=2, ensure_ascii=True) + "\n")
    # Protect this installer-managed file from launch-time config cleaners.
    path.chmod(stat.S_IREAD)


def _is_named_pack(identifier: str, fragment: str) -> bool:
    return identifier.startswith("file/") and fragment.casefold() in identifier.casefold()


def _arrange_packs(current: list[str], interface_pack: str) -> list[str]:
    """Return Minecraft's low-to-high priority order.

    The resource-pack screen displays this list in reverse.  Mod-provided
    resources therefore belong immediately after vanilla, while GUI overlays
    are inserted around Colourful Containers.
    """
    mod_ids = [item for item in current if not item.startswith("file/") and item != "vanilla"]
    regular = [item for item in current if item.startswith("file/")]
    special = [
        item for item in regular
        if _is_named_pack(item, "overgrown flowery gui")
        or _is_named_pack(item, "extra flowery gui")
        or _is_named_pack(item, "simple hotbar")
    ]
    regular = [item for item in regular if item not in special]

    if interface_pack == "flowery":
        below = [item for item in special if _is_named_pack(item, "overgrown flowery gui")]
        above = [item for item in special if _is_named_pack(item, "extra flowery gui")]
    elif interface_pack == "simple_hotbar":
        below = [item for item in special if _is_named_pack(item, "simple hotbar")]
        above = []
    else:
        below = above = []

    anchor = next((index for index, item in enumerate(regular) if _is_named_pack(item, "colourful containers")), len(regular))
    regular[anchor:anchor] = below
    anchor += len(below) + (1 if anchor < len(regular) else 0)
    regular[anchor:anchor] = above
    return ["vanilla", *dict.fromkeys(mod_ids), *regular]


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
    if isinstance(value, list) and value and all(isinstance(item, int) for item in value):
        return expected in value or len(value) == 2 and min(value) <= expected <= max(value)
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
    activation_ids: tuple[str, ...] = (),
    interface_pack: str = "flowery",
    profile_packs: tuple[str, ...] = (),
) -> None:
    path = game_dir / "options.txt"
    lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    activation_ids = tuple(dict.fromkeys((*activation_ids, *MOD_PACK_IDS)))
    managed = {_quote(pack.file_name) for pack in packs} | set(activation_ids)
    selected_names = set(profile_packs)
    selected = [pack for pack in packs if enabled and (pack.active or pack.file_name in selected_names) and (game_dir / RESOURCEPACKS_DIR_NAME / pack.file_name).is_file()]
    if enabled and not profile_packs:
        for pack in packs:
            name = pack.file_name.casefold()
            chosen = interface_pack == "flowery" and "flowery gui" in name or interface_pack == "simple_hotbar" and "simple hotbar" in name
            if chosen and (game_dir / RESOURCEPACKS_DIR_NAME / pack.file_name).is_file() and pack not in selected:
                selected.append(pack)
    wanted = [_quote(pack.file_name) for pack in selected]
    if enabled:
        wanted.extend(identifier for identifier in activation_ids if identifier not in wanted)
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
        if key == "resourcePacks" and enabled:
            merged = _arrange_packs(merged, interface_pack)
            _write_override_config(game_dir, merged)
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
