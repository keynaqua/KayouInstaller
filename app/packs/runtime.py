from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from logger import error
from utils.files import FileProgressCallback, VerifiedDownload, download_many, file_hash, safe_relative_path, validate_digest, validate_format, validate_url
from utils.progress import ProgressCallback, RangedProgress


@dataclass(frozen=True)
class Pack:
    file_name: str
    download_url: str
    sha256: str
    active: bool
    order: int


def _required(entry: dict, field: str, label: str) -> str:
    value = entry.get(field)
    if not isinstance(value, str) or not value.strip():
        raise RuntimeError(f"{label}: champ '{field}' invalide")
    return value.strip()


def parse_pack_manifest(
    data: object,
    manifest_name: str,
    default_active: bool,
    sections: tuple[str, ...] = ("packs",),
    single_active: bool = False,
) -> list[Pack]:
    if not isinstance(data, dict):
        raise RuntimeError(f"Le manifest {manifest_name} doit etre un objet JSON")
    validate_format(data, manifest_name)
    raw = next((data[name] for name in sections if name in data), None)
    if not isinstance(raw, list):
        raise RuntimeError(f"Le manifest {manifest_name} doit contenir une liste '{sections[0]}'")
    packs = []
    for index, entry in enumerate(raw, start=1):
        label = f"{manifest_name}: {sections[0]}[{index}]"
        if not isinstance(entry, dict):
            raise RuntimeError(f"{label} doit etre un objet")
        file_name = _required(entry, "file_name", label)
        if len(safe_relative_path(file_name, label).parts) != 1:
            raise RuntimeError(f"{label}: file_name invalide")
        order = entry.get("order", index)
        if not isinstance(order, int) or isinstance(order, bool):
            raise RuntimeError(f"{label}: champ 'order' invalide")
        url = _required(entry, "download_url", label)
        packs.append(Pack(
            file_name,
            validate_url(url, label),
            validate_digest(_required(entry, "sha256", label), "sha256", label),
            entry.get("active", default_active) is True,
            order,
        ))
    names = [pack.file_name.lower() for pack in packs]
    if len(names) != len(set(names)):
        raise RuntimeError(f"Le manifest {manifest_name} contient des fichiers dupliques")
    packs.sort(key=lambda pack: pack.order)
    if single_active and sum(pack.active for pack in packs) > 1:
        raise RuntimeError(f"Le manifest {manifest_name} ne peut activer qu'un pack")
    return packs


def sync_packs(
    target_dir: Path,
    packs: list[Pack],
    log: Callable[[str], None],
    progress_callback: ProgressCallback | None,
    download_callback: FileProgressCallback | None,
    progress_start: int,
    progress_end: int,
) -> list[str]:
    target_dir.mkdir(parents=True, exist_ok=True)
    progress = RangedProgress(progress_callback, progress_start, progress_end, len(packs))
    downloads = []
    for pack in packs:
        target = target_dir / pack.file_name
        if target.exists() and file_hash(target, "sha256") == pack.sha256:
            log(f"OK {pack.file_name}")
            progress.advance()
            continue
        log(f"{'Update' if target.exists() else 'Install'} {pack.file_name}")
        downloads.append(VerifiedDownload(pack.download_url, target, "sha256", pack.sha256))
    missing = download_many(downloads, download_callback, lambda _item: progress.advance(), True, True)
    for item in missing:
        error(f"Fichier introuvable, ignore: {item.target.name}")
        progress.advance()
    if missing:
        error("Si le probleme persiste, contacte @aquakeyn sur Discord.")
    progress.finish()
    return [
        pack.file_name
        for pack in packs
        if (target := target_dir / pack.file_name).is_file()
        and file_hash(target, "sha256") == pack.sha256
    ]
