import json
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

from config import (
    JAVA_COMMAND,
    LATEST_VERSION,
    NEOFORGE_INSTALL_CLIENT_ARGS,
    NEOFORGE_METADATA_URL,
    NEOFORGE_VERSION_ID_PREFIX,
    get_minecraft_dir,
    get_neoforge_installer_name,
    get_neoforge_installer_url,
    get_neoforge_version_prefix,
)
from logger import neoforge, success
from utils.http import download_file, get_text
from utils.files import FileProgressCallback, bind_progress


def _parse_version_tuple(version: str) -> tuple[int, ...]:
    parts = []
    for part in version.replace("-beta", "").split("."):
        try:
            parts.append(int(part))
        except ValueError:
            parts.append(0)
    return tuple(parts)


def _extract_neoforge_version(version_id: str) -> str | None:
    if version_id.startswith(NEOFORGE_VERSION_ID_PREFIX):
        return version_id[len(NEOFORGE_VERSION_ID_PREFIX):]
    return None


def _version_matches_mc(neoforge_version: str, mc_version: str) -> bool:
    return neoforge_version.startswith(get_neoforge_version_prefix(mc_version))


def get_latest_neoforge_version(mc_version: str) -> str:
    root = ET.fromstring(get_text(NEOFORGE_METADATA_URL))
    versions = [
        node.text.strip()
        for node in root.findall("./versioning/versions/version")
        if node.text and _version_matches_mc(node.text.strip(), mc_version)
    ]
    if not versions:
        raise RuntimeError(f"Aucune version NeoForge trouvee pour Minecraft {mc_version}.")
    return max(versions, key=_parse_version_tuple)


def find_installed_neoforge_version(mc_dir: Path, mc_version: str) -> str | None:
    versions_dir = mc_dir / "versions"
    if not versions_dir.exists():
        return None

    found = []
    for version_json in versions_dir.glob("*/*.json"):
        try:
            content = json.loads(version_json.read_text(encoding="utf-8"))
        except Exception:
            continue

        version = _extract_neoforge_version(str(content.get("id", "")))
        if version and _version_matches_mc(version, mc_version):
            found.append(version)

    return max(found, key=_parse_version_tuple) if found else None


def get_installed_neoforge_version_id(mc_dir: Path, mc_version: str) -> str:
    versions_dir = mc_dir / "versions"
    if not versions_dir.exists():
        raise FileNotFoundError("Le dossier versions de Minecraft est introuvable.")

    candidates = [
        (version, entry.name)
        for entry in versions_dir.iterdir()
        if entry.is_dir()
        for version in [_extract_neoforge_version(entry.name)]
        if version and _version_matches_mc(version, mc_version)
    ]
    if not candidates:
        raise RuntimeError(
            f"Aucune version NeoForge installee trouvee pour Minecraft {mc_version}."
        )

    candidates.sort(key=lambda item: _parse_version_tuple(item[0]))
    return candidates[-1][1]


def run_neoforge_installer(
    jar_path: Path,
    mc_dir: Path,
    java_command: str = JAVA_COMMAND,
) -> None:
    for args in NEOFORGE_INSTALL_CLIENT_ARGS:
        cmd = [java_command, "-jar", str(jar_path), *args, str(mc_dir)]
        neoforge(f"Lancement de l'installateur NeoForge ({' '.join(args)})...")
        result = subprocess.run(cmd, check=False)
        if result.returncode == 0:
            return

    raise RuntimeError("Echec de l'installation NeoForge en mode client.")


def resolve_neoforge_version(mc_version: str, requested_version: str) -> str:
    if requested_version.lower() == LATEST_VERSION:
        return get_latest_neoforge_version(mc_version)
    if not _version_matches_mc(requested_version, mc_version):
        raise RuntimeError(
            f"NeoForge {requested_version} ne correspond pas a Minecraft {mc_version}."
        )
    return requested_version


def ensure_neoforge_installed(
    mc_version: str,
    requested_version: str = LATEST_VERSION,
    download_callback: FileProgressCallback | None = None,
    java_command: str = JAVA_COMMAND,
) -> str:
    mc_dir = get_minecraft_dir()

    neoforge(f"Dossier Minecraft : {mc_dir}")
    neoforge(f"Version Minecraft cible : {mc_version}")

    expected_version = resolve_neoforge_version(mc_version, requested_version)
    installed_version = find_installed_neoforge_version(mc_dir, mc_version)

    neoforge(f"NeoForge attendu : {expected_version}")
    neoforge(f"NeoForge installe : {installed_version or 'aucun'}")

    if installed_version == expected_version:
        success("NeoForge est deja installe dans la bonne version.")
        return get_installed_neoforge_version_id(mc_dir, mc_version)

    neoforge("NeoForge absent ou pas a jour. Installation en cours...")
    with tempfile.TemporaryDirectory() as tmp_dir:
        jar_path = Path(tmp_dir) / get_neoforge_installer_name(expected_version)
        download_file(
            get_neoforge_installer_url(expected_version),
            jar_path,
            callback=bind_progress(jar_path.name, download_callback),
        )
        run_neoforge_installer(jar_path, mc_dir, java_command)

    installed_version = find_installed_neoforge_version(mc_dir, mc_version)
    if installed_version != expected_version:
        raise RuntimeError(
            "NeoForge ne semble pas s'etre installe correctement "
            f"(attendu: {expected_version}, detecte: {installed_version or 'aucun'})"
        )

    version_id = get_installed_neoforge_version_id(mc_dir, mc_version)
    neoforge(f"Version NeoForge retenue : {version_id}")
    success("NeoForge installe / mis a jour avec succes.")
    return version_id
