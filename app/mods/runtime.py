from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

from logger import error, extra, info, missing, mods, outdated, success, uptodate
from utils.files import FileProgressCallback, VerifiedDownload, download_many, file_hash, safe_relative_path, validate_digest, validate_format, validate_url
from utils.http import get_json
from utils.progress import ProgressCallback, RangedProgress

from .detect import DetectionReport, InstalledMod, detect_mods, ensure_sha1

MOD_PROGRESS_START = 30
MOD_PROGRESS_END = 70


@dataclass
class ManifestMod:
    mod_id: str
    version: str
    download_url: str
    file_name: str
    sha1: str


def _ensure_windows_10_or_11() -> None:
    if sys.platform != "win32":
        raise RuntimeError("KayouInstaller ne supporte que Windows.")


def _required_string(entry: dict, field: str, label: str) -> str:
    value = entry.get(field)
    if not isinstance(value, str) or not value.strip():
        raise RuntimeError(f"{label}: champ '{field}' invalide")
    return value.strip()


def load_mod_manifest(manifest_url: str, cache_version: str = "") -> tuple[list[ManifestMod], set[str], set[str]]:
    data = get_json(manifest_url, cache_key=cache_version)
    if not isinstance(data, dict):
        raise RuntimeError("Le manifest des mods doit etre un objet JSON")
    validate_format(data, "mods.json")

    raw_mods = data.get("mods")
    if not isinstance(raw_mods, list):
        raise RuntimeError("Le manifest doit contenir une liste 'mods'")

    manifest_mods: list[ManifestMod] = []
    for index, entry in enumerate(raw_mods, start=1):
        if not isinstance(entry, dict):
            raise RuntimeError(f"mods[{index}] doit etre un objet")
        label = f"mods[{index}]"
        raw_url = entry.get("download_url", "")
        if not isinstance(raw_url, str):
            raise RuntimeError(f"{label}: champ 'download_url' invalide")
        mod = ManifestMod(
            mod_id=_required_string(entry, "id", label),
            version=_required_string(entry, "version", label),
            download_url=validate_url(raw_url.strip(), label) if raw_url.strip() else "",
            file_name=_required_string(entry, "file_name", label),
            sha1=validate_digest(_required_string(entry, "sha1", label), "sha1", label),
        )
        if len(safe_relative_path(mod.file_name, label).parts) != 1 or not mod.file_name.lower().endswith(".jar"):
            raise RuntimeError(f"{label}: file_name invalide")
        manifest_mods.append(mod)

    ids = [mod.mod_id for mod in manifest_mods]
    names = [mod.file_name.lower() for mod in manifest_mods]
    if len(ids) != len(set(ids)):
        raise RuntimeError("Le manifest contient des ids dupliques")
    if len(names) != len(set(names)):
        raise RuntimeError("Le manifest contient des noms de fichiers dupliques")

    return (
        manifest_mods,
        _load_rule_ids(data, "blacklist"),
        _load_rule_ids(data, "safe_mode"),
    )


def _load_rule_ids(data: dict, section: str) -> set[str]:
    raw_rules = data.get(section, [])
    if not isinstance(raw_rules, list):
        raise RuntimeError(f"'{section}' doit etre une liste")

    ids: set[str] = set()
    for index, entry in enumerate(raw_rules, start=1):
        if isinstance(entry, str) and entry.strip():
            ids.add(entry.strip())
            continue
        if isinstance(entry, dict):
            ids.add(_required_string(entry, "id", f"{section}[{index}]"))
            continue
        raise RuntimeError(f"{section}[{index}] doit etre une chaine ou un objet")
    return ids


def _remove_mod_ids(mods_list: list[InstalledMod], mod_ids: set[str], label: str) -> None:
    if not mod_ids:
        return

    removed = 0
    for mod in mods_list:
        if mod.mod_id not in mod_ids:
            continue
        if mod.file_path.exists():
            info(f" - [MODS] Remove {label}: {mod.file_path.name}")
            mod.file_path.unlink()
            removed += 1

    if removed:
        success(f"{label}: {removed} mod(s) supprime(s)")


def _report_broken_files(report: DetectionReport) -> None:
    if not report.broken_files:
        return
    error("Fichiers .jar invalides detectes:")
    for file_path, reason in report.broken_files:
        extra(f"{file_path.name}: {reason}")


def _index_by_mod_id(mods_list: list[InstalledMod]) -> dict[str, list[InstalledMod]]:
    index: dict[str, list[InstalledMod]] = {}
    for mod in mods_list:
        index.setdefault(mod.mod_id, []).append(mod)
    return index


def _sync_manifest_mods(
    mods_dir: Path,
    desired_mods: list[ManifestMod],
    installed_mods: list[InstalledMod] | None = None,
    progress_callback: ProgressCallback | None = None,
    download_callback: FileProgressCallback | None = None,
    progress_start: int = MOD_PROGRESS_START,
    progress_end: int = MOD_PROGRESS_END,
) -> list[str]:
    installed = _index_by_mod_id(installed_mods if installed_mods is not None else detect_mods(mods_dir).mods)
    ranged_progress = RangedProgress(progress_callback, progress_start, progress_end, len(desired_mods))
    downloads = []
    old_files: dict[Path, list[Path]] = {}
    missing_url = False

    for desired in desired_mods:
        matches = installed.get(desired.mod_id, [])
        up_to_date = next(
            (
                mod
                for mod in matches
                if mod.version == desired.version and ensure_sha1(mod) == desired.sha1
            ),
            None,
        )

        if up_to_date:
            uptodate(f"{desired.mod_id} ({desired.version})")
            for duplicate in matches:
                if duplicate.file_path != up_to_date.file_path and duplicate.file_path.exists():
                    info(f" - [MODS] Remove duplicate: {duplicate.file_path.name}")
                    duplicate.file_path.unlink()
            ranged_progress.advance()
            continue

        if not desired.download_url:
            error(f"Fichier sans URL et introuvable, ignore: {desired.file_name}")
            missing_url = True
            ranged_progress.advance()
            continue

        target = mods_dir / desired.file_name
        for old_mod in matches:
            if old_mod.file_path.exists():
                outdated(f"UPDATE {desired.mod_id}: {old_mod.version} -> {desired.version}")

        if not matches:
            missing(f"INSTALL {desired.mod_id} -> {desired.version}")

        downloads.append(
            VerifiedDownload(desired.download_url, target, "sha1", desired.sha1)
        )
        old_files[target] = [mod.file_path for mod in matches if mod.file_path != target]

    def complete(item: VerifiedDownload) -> None:
        for old_file in old_files[item.target]:
            old_file.unlink(missing_ok=True)
        ranged_progress.advance()

    missing_files = download_many(downloads, download_callback, complete, True)
    for item in missing_files:
        error(f"Fichier introuvable, ignore: {item.target.name}")
        ranged_progress.advance()
    if missing_files or missing_url:
        error("Si le probleme persiste, contacte @aquakeyn sur Discord.")

    ranged_progress.finish()
    return [
        mod.file_name
        for mod in desired_mods
        if (target := mods_dir / mod.file_name).is_file()
        and file_hash(target, "sha1") == mod.sha1
    ]


def update_mods(
    mods_dir: str | Path,
    modpack_key: str,
    safe_mode: bool = False,
    progress_callback: ProgressCallback | None = None,
    download_callback: FileProgressCallback | None = None,
    manifest: tuple[list[ManifestMod], set[str], set[str]] | None = None,
) -> list[str]:
    _ensure_windows_10_or_11()

    mods_path = Path(mods_dir)
    mods_path.mkdir(parents=True, exist_ok=True)

    mods("Chargement du manifest des mods...")
    manifest_mods, blacklist_ids, safe_mode_ids = manifest or load_mod_manifest(modpack_key)
    report = detect_mods(mods_path)
    _report_broken_files(report)

    mods("Suppression des mods blacklistes...")
    _remove_mod_ids(report.mods, blacklist_ids, "blacklist")

    safe_mode_enabled = safe_mode and bool(safe_mode_ids)
    if safe_mode_enabled:
        mods("Application du safe mode...")
        _remove_mod_ids(report.mods, safe_mode_ids, "safe mode")

    excluded_ids = safe_mode_ids if safe_mode_enabled else set()
    wanted = [mod for mod in manifest_mods if mod.mod_id not in excluded_ids]

    mods("Synchronisation des mods du manifest...")
    installed = [mod for mod in report.mods if mod.file_path.exists()]
    files = _sync_manifest_mods(
        mods_path,
        wanted,
        installed_mods=installed,
        progress_callback=progress_callback,
        download_callback=download_callback,
    )

    success("Mods synchronises avec succes !")
    return files
