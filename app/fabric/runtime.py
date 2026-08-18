import json
import subprocess
import tempfile
from pathlib import Path

from config import (
    FABRIC_INSTALLER_META_URL,
    FABRIC_LOADER_PREFIX,
    FABRIC_META_URL,
    JAVA_COMMAND,
    LATEST_VERSION,
    get_fabric_installer_name,
    get_fabric_installer_url,
    get_minecraft_dir,
)
from logger import fabric, success
from utils.http import download_file, get_json
from utils.files import FileProgressCallback, bind_progress


def _parse_version_tuple(version: str) -> tuple[int, ...]:
    parts = []
    for part in version.split("."):
        try:
            parts.append(int(part))
        except ValueError:
            parts.append(0)
    return tuple(parts)


def _extract_loader_version(version_id: str, mc_version: str) -> str | None:
    suffix = f"-{mc_version}"
    if version_id.startswith(FABRIC_LOADER_PREFIX) and version_id.endswith(suffix):
        return version_id[len(FABRIC_LOADER_PREFIX):-len(suffix)]
    return None


def find_installed_fabric_loader(mc_dir: Path, mc_version: str) -> str | None:
    versions_dir = mc_dir / "versions"
    if not versions_dir.exists():
        return None

    found_versions = []
    for version_json in versions_dir.glob("*/*.json"):
        try:
            content = json.loads(version_json.read_text(encoding="utf-8"))
        except Exception:
            continue

        version_id = str(content.get("id", ""))
        inherits_from = str(content.get("inheritsFrom", ""))
        loader_version = _extract_loader_version(version_id, mc_version)
        if loader_version and (inherits_from == mc_version or version_id.endswith(f"-{mc_version}")):
            found_versions.append(loader_version)

    return max(found_versions, key=_parse_version_tuple) if found_versions else None


def get_installed_fabric_version_id(mc_dir: Path, mc_version: str) -> str:
    versions_dir = mc_dir / "versions"
    if not versions_dir.exists():
        raise FileNotFoundError("Le dossier versions de Minecraft est introuvable.")

    candidates = [
        (loader_version, entry.name)
        for entry in versions_dir.iterdir()
        if entry.is_dir()
        for loader_version in [_extract_loader_version(entry.name, mc_version)]
        if loader_version
    ]
    if not candidates:
        raise RuntimeError(
            f"Aucune version Fabric installee trouvee pour Minecraft {mc_version}."
        )

    candidates.sort(key=lambda item: _parse_version_tuple(item[0]))
    return candidates[-1][1]


def get_latest_loader_version(mc_version: str) -> str:
    data = get_json(f"{FABRIC_META_URL}/{mc_version}")
    if not data:
        raise RuntimeError(f"Aucune version Fabric trouvee pour Minecraft {mc_version}")
    return data[0]["loader"]["version"]


def get_latest_installer_version() -> str:
    data = get_json(FABRIC_INSTALLER_META_URL)
    if not data:
        raise RuntimeError("Impossible de recuperer la version de l'installateur Fabric")
    return data[0]["version"]


def run_fabric_installer(
    jar_path: Path,
    mc_dir: Path,
    mc_version: str,
    loader_version: str,
    java_command: str = JAVA_COMMAND,
) -> None:
    result = subprocess.run(
        [
            java_command,
            "-jar",
            str(jar_path),
            "client",
            "-dir",
            str(mc_dir),
            "-mcversion",
            mc_version,
            "-loader",
            loader_version,
            "-noprofile",
        ],
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Echec de l'installation Fabric (code retour {result.returncode})")


def _list_installed_fabric_versions(mc_dir: Path, mc_version: str) -> list[str]:
    versions_dir = mc_dir / "versions"
    if not versions_dir.exists():
        return []

    suffix = f"-{mc_version}"
    return sorted(
        entry.name
        for entry in versions_dir.iterdir()
        if entry.is_dir()
        and entry.name.startswith(FABRIC_LOADER_PREFIX)
        and entry.name.endswith(suffix)
    )


def resolve_loader_version(mc_version: str, requested_version: str) -> str:
    if requested_version.lower() == LATEST_VERSION:
        return get_latest_loader_version(mc_version)
    return requested_version


def ensure_fabric_installed(
    mc_version: str,
    requested_version: str = LATEST_VERSION,
    download_callback: FileProgressCallback | None = None,
    java_command: str = JAVA_COMMAND,
) -> str:
    mc_dir = get_minecraft_dir()

    fabric(f"Dossier Minecraft : {mc_dir}")
    fabric(f"Version Minecraft cible : {mc_version}")

    expected_loader = resolve_loader_version(mc_version, requested_version)
    installed_loader = find_installed_fabric_loader(mc_dir, mc_version)

    fabric(f"Loader Fabric attendu : {expected_loader}")
    fabric(f"Loader Fabric installe : {installed_loader or 'aucun'}")

    if installed_loader == expected_loader:
        success("Fabric est deja installe dans la bonne version.")
        return get_installed_fabric_version_id(mc_dir, mc_version)

    fabric("Fabric absent ou pas a jour. Installation en cours...")
    installer_version = get_latest_installer_version()

    with tempfile.TemporaryDirectory() as tmp_dir:
        jar_path = Path(tmp_dir) / get_fabric_installer_name(installer_version)
        download_file(
            get_fabric_installer_url(installer_version),
            jar_path,
            callback=bind_progress(jar_path.name, download_callback),
        )
        fabric(f"Lancement de l'installateur Fabric {installer_version}...")
        run_fabric_installer(jar_path, mc_dir, mc_version, expected_loader, java_command)

    installed_loader = find_installed_fabric_loader(mc_dir, mc_version)
    fabric_versions = _list_installed_fabric_versions(mc_dir, mc_version)
    if fabric_versions:
        fabric("Versions Fabric detectees apres installation :")
        for version_id in fabric_versions:
            fabric(f" - {version_id}")

    if installed_loader != expected_loader:
        raise RuntimeError(
            "Fabric ne semble pas s'etre installe correctement "
            f"(attendu: {expected_loader}, detecte: {installed_loader or 'aucun'})"
        )

    version_id = get_installed_fabric_version_id(mc_dir, mc_version)
    fabric(f"Version Fabric retenue : {version_id}")
    success("Fabric installe / mis a jour avec succes.")
    return version_id
