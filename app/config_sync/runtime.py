from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from config import CONFIG_DIR_NAME, SHORT_HTTP_RETRIES, SHORT_HTTP_TIMEOUT, get_install_subdir
from logger import info, success
from utils.files import FileProgressCallback, VerifiedDownload, download_many, safe_relative_path, validate_digest, validate_format, validate_url
from utils.http import get_json


class ConfigSyncError(RuntimeError):
    pass


@dataclass(frozen=True)
class ConfigFile:
    path: Path
    sha256: str
    mode: str
    enabled: bool
    download_url: str


@dataclass(frozen=True)
class ConfigManifest:
    files: list[ConfigFile]


@dataclass(frozen=True)
class ConfigResult:
    files: list[str]
    managed: list[str]


def _required(entry: dict, field: str, label: str) -> str:
    value = entry.get(field)
    if not isinstance(value, str) or not value.strip():
        raise RuntimeError(f"{label}: champ '{field}' invalide")
    return value.strip()


def load_config_manifest(manifest_url: str, cache_version: str = "") -> ConfigManifest | None:
    if not manifest_url:
        return None
    data = get_json(manifest_url, timeout=SHORT_HTTP_TIMEOUT, retries=SHORT_HTTP_RETRIES, cache_key=cache_version)
    if not isinstance(data, dict):
        raise RuntimeError("configs.json doit être un objet JSON")
    validate_format(data, "configs.json")
    raw_files = data.get("files", [])
    if not isinstance(raw_files, list):
        raise RuntimeError("configs.json: files doit être une liste")
    if data.get("directories"):
        raise RuntimeError("configs.json: les dossiers doivent être développés en fichiers par build_catalog.py")

    files = []
    for index, entry in enumerate(raw_files, start=1):
        label = f"files[{index}]"
        if not isinstance(entry, dict):
            raise RuntimeError(f"{label}: entrée invalide")
        path = safe_relative_path(_required(entry, "path", label), label)
        mode = str(entry.get("mode", "preserve")).strip().lower()
        if mode not in {"managed", "preserve", "optional"}:
            raise RuntimeError(f"{label}: mode invalide")
        files.append(ConfigFile(
            path=path,
            sha256=validate_digest(_required(entry, "sha256", label), "sha256", label),
            mode=mode,
            enabled=entry.get("enabled") is True,
            download_url=validate_url(_required(entry, "download_url", label), label),
        ))
    paths = [item.path.as_posix().casefold() for item in files]
    if len(paths) != len(set(paths)):
        raise RuntimeError("configs.json contient des chemins dupliqués")
    return ConfigManifest(files)


def sync_config_folder(
    installation_name: str,
    target_subdir: str = CONFIG_DIR_NAME,
    download_callback: FileProgressCallback | None = None,
    manifest: ConfigManifest | None = None,
) -> ConfigResult:
    target_root = get_install_subdir(installation_name, target_subdir)
    target_root.mkdir(parents=True, exist_ok=True)
    if manifest is None:
        success("Aucune config distante à synchroniser.")
        return ConfigResult([], [])

    try:
        installed = []
        managed = []
        downloads = []
        for item in manifest.files:
            target = target_root / item.path
            if item.mode == "optional" and not item.enabled:
                info(f" - [CONFIG] Optionnelle ignorée: {item.path}")
                continue
            if item.mode in {"preserve", "optional"} and target.exists():
                info(f" - [CONFIG] Conservée: {item.path}")
            else:
                info(f" - [CONFIG] Synchronisation: {item.path}")
                downloads.append(VerifiedDownload(item.download_url, target, "sha256", item.sha256))
            relative = (Path(CONFIG_DIR_NAME) / item.path).as_posix()
            installed.append(relative)
            if item.mode == "managed":
                managed.append(relative)
        download_many(downloads, download_callback)
        success("Configs synchronisées avec succès.")
        return ConfigResult(installed, managed)
    except Exception as exc:
        raise ConfigSyncError(f"Synchronisation des configs impossible: {exc}") from exc
