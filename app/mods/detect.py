from __future__ import annotations

import hashlib
import json
import tomllib
import zipfile
from dataclasses import dataclass, field
from email.parser import BytesParser
from pathlib import Path
from typing import Any

from config import JAR_GLOB, MOD_HASH_CHUNK_SIZE


@dataclass
class InstalledMod:
    mod_id: str
    version: str
    file_path: Path
    sha1: str | None = None


@dataclass
class DetectionReport:
    mods: list[InstalledMod] = field(default_factory=list)
    broken_files: list[tuple[Path, str]] = field(default_factory=list)


def sha1_file(path: Path) -> str:
    h = hashlib.sha1()
    with path.open("rb") as file:
        while chunk := file.read(MOD_HASH_CHUNK_SIZE):
            h.update(chunk)
    return h.hexdigest()


def ensure_sha1(mod: InstalledMod) -> str:
    if mod.sha1 is None:
        mod.sha1 = sha1_file(mod.file_path)
    return mod.sha1


def _escape_control_chars(text: str) -> str:
    result: list[str] = []
    in_string = False
    escaped = False

    for char in text:
        if escaped:
            result.append(char)
            escaped = False
            continue
        if char == "\\":
            result.append(char)
            escaped = True
            continue
        if char == '"':
            result.append(char)
            in_string = not in_string
            continue
        if in_string and char in ("\n", "\r", "\t"):
            result.append({"\n": "\\n", "\r": "\\r", "\t": "\\t"}[char])
            continue
        result.append(char)

    return "".join(result)


def _load_json_tolerant(text: str) -> dict[str, Any] | list[Any]:
    text = text.replace("\ufeff", "")
    for candidate in (text, _escape_control_chars(text)):
        try:
            return json.loads(candidate, strict=False)
        except json.JSONDecodeError:
            pass
    return json.loads(_escape_control_chars(text))


def _fabric_mods(jar: zipfile.ZipFile) -> list[tuple[str, str]]:
    with jar.open("fabric.mod.json") as file:
        data = _load_json_tolerant(file.read().decode("utf-8-sig", errors="replace"))
    if isinstance(data, list):
        entries = [item for item in data if isinstance(item, dict)]
    else:
        entries = [data] if isinstance(data, dict) else []
    return [_metadata(entry, "fabric.mod.json") for entry in entries]


def _manifest_version(jar: zipfile.ZipFile) -> str | None:
    try:
        with jar.open("META-INF/MANIFEST.MF") as file:
            return BytesParser().parsebytes(file.read()).get("Implementation-Version")
    except KeyError:
        return None


def _neoforge_mods(jar: zipfile.ZipFile, metadata_path: str) -> list[tuple[str, str]]:
    with jar.open(metadata_path) as file:
        data = tomllib.loads(file.read().decode("utf-8-sig", errors="replace"))
    entries = data.get("mods", [])
    if not isinstance(entries, list):
        raise RuntimeError(f"{metadata_path} inexploitable")
    jar_version = _manifest_version(jar)
    mods = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        mod_id, version = _metadata(entry, metadata_path, "modId")
        if version == "${file.jarVersion}":
            if not jar_version:
                raise RuntimeError(f"Implementation-Version manquante pour {mod_id}")
            version = jar_version
        mods.append((mod_id, version))
    return mods


def _metadata(data: dict[str, Any], source: str, id_field: str = "id") -> tuple[str, str]:
    mod_id = data.get(id_field)
    version = data.get("version", "1")
    if not isinstance(mod_id, str) or not mod_id.strip():
        raise RuntimeError(f"id manquant dans {source}")
    if not isinstance(version, str) or not version.strip():
        raise RuntimeError(f"version manquante dans {source}")
    return mod_id.strip(), version.strip()


def _read_mods(path: Path) -> list[tuple[str, str]]:
    with zipfile.ZipFile(path) as jar:
        names = set(jar.namelist())
        if "fabric.mod.json" in names:
            return _fabric_mods(jar)
        for metadata_path in ("META-INF/neoforge.mods.toml", "META-INF/mods.toml"):
            if metadata_path in names:
                return _neoforge_mods(jar, metadata_path)
    raise RuntimeError("metadata Fabric ou NeoForge introuvable")


def detect_mods(mods_dir: str | Path) -> DetectionReport:
    mods_path = Path(mods_dir)
    report = DetectionReport()

    if not mods_path.exists():
        return report
    if not mods_path.is_dir():
        raise NotADirectoryError(f"Dossier mods invalide: {mods_path}")

    for jar_path in sorted(mods_path.glob(JAR_GLOB)):
        try:
            for mod_id, version in _read_mods(jar_path):
                report.mods.append(
                    InstalledMod(
                        mod_id=mod_id,
                        version=version,
                        file_path=jar_path,
                    )
                )
        except Exception as exc:
            report.broken_files.append((jar_path, str(exc)))

    return report
