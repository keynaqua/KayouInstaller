import os
from pathlib import Path

# ----- Versions ----- #
JAVA_MAJOR = 21

VERSION = "4.0.0"

APP_BASENAME = "KayouInstaller"

MODPACK_CATALOG_URL = "https://kayou-modpacks.pages.dev/catalog.json"

# ----- Paths ----- #
MINECRAFT_DIR_NAME = ".minecraft"
INSTALLATIONS_DIR_NAME = ".installations"
LAUNCHER_PROFILES_FILE = "launcher_profiles.json"
MODS_DIR_NAME = "mods"
CONFIG_DIR_NAME = "config"
RESOURCEPACKS_DIR_NAME = "resourcepacks"
SHADERPACKS_DIR_NAME = "shaderpacks"
DATAPACKS_DIR_NAME = "datapacks"
DEFAULT_INSTALL_SUBDIRS = (
    MODS_DIR_NAME,
    CONFIG_DIR_NAME,
    RESOURCEPACKS_DIR_NAME,
    SHADERPACKS_DIR_NAME,
    "saves",
    "logs",
    "crash-reports",
)
JAVA_DEFAULT_ROOT = Path(r"C:\Program Files\Eclipse Adoptium")
JAVA_COMMAND = "java"
JAVA_BIN_DIR_NAME = "bin"
JAVA_EXE_NAME = "java.exe"
JAR_SUFFIX = ".jar"
JAR_GLOB = f"*{JAR_SUFFIX}"
MSI_SUFFIX = ".msi"
LOG_SUFFIX = ".log"
UPDATE_SCRIPT_NAME = "update_tmp.bat"
PENDING_UPDATE_SUFFIX = ".update.exe"
PARTIAL_DOWNLOAD_SUFFIX = ".part"
INSTALLER_STATE_DIR_NAME = ".kayou"
INSTALLER_INVENTORY_FILE = "installation.json"
CACHE_DIR_NAME = APP_BASENAME
CATALOG_CACHE_FILE = "catalog.json"
# Le catalogue est la petite ressource d'invalidation : une tentative par
# lancement permet de publier immédiatement une nouvelle revision. En cas
# d'échec réseau, catalog.runtime reprend la dernière copie locale valide.
CATALOG_CACHE_TTL = 60
HTTP_CACHE_DIR_NAME = "http"
HTTP_CACHE_TTL = 60 * 60
HTTP_NEGATIVE_CACHE_TTL = 15 * 60

# ----- AUMID ----- #
AUMID = "Microsoft.4297127D64EC6_8wekyb3d8bbwe!Minecraft"

# ----- URLs ----- #
ADOPTIUM_API_URL = "https://api.adoptium.net/v3/assets/latest"
FABRIC_META_URL = "https://meta.fabricmc.net/v2/versions/loader"
FABRIC_INSTALLER_META_URL = "https://meta.fabricmc.net/v2/versions/installer"
FABRIC_MAVEN_URL = "https://maven.fabricmc.net/net/fabricmc/fabric-installer"
FABRIC_LOADER_PREFIX = "fabric-loader-"
NEOFORGE_MAVEN_URL = "https://maven.neoforged.net/releases/net/neoforged/neoforge"
NEOFORGE_METADATA_URL = f"{NEOFORGE_MAVEN_URL}/maven-metadata.xml"
NEOFORGE_VERSION_PREFIX_BY_MC = {
    "1.20.1": "47.1.",
    "1.21.1": "21.1.",
}
NEOFORGE_VERSION_ID_PREFIX = "neoforge-"
NEOFORGE_INSTALL_CLIENT_ARGS = (
    ("--installClient",),
    ("--install-client",),
)

# ----- HTTP ----- #
HTTP_JSON_TIMEOUT = 20
HTTP_JSON_RETRIES = 3
HTTP_JSON_RETRY_DELAY = 1.5
HTTP_DOWNLOAD_TIMEOUT = 60
HTTP_DOWNLOAD_RETRIES = 4
HTTP_DOWNLOAD_RETRY_DELAY = 2.0
HTTP_CHUNK_SIZE = 1024 * 64
DOWNLOAD_WORKERS = 2
DOWNLOAD_PROGRESS_INTERVAL = 0.1
HASH_CHUNK_SIZE = 1024 * 1024
MOD_HASH_CHUNK_SIZE = 1024 * 64
BYTES_PER_GIB = 1024 ** 3
JAVA_RAM_RATIO = 0.65
JAVA_RAM_MIN_GB = 4
SHORT_HTTP_TIMEOUT = 5
SHORT_HTTP_RETRIES = 1
UPDATE_HTTP_TIMEOUT = 4
UPDATE_HTTP_RETRIES = 1

# ----- GUI ----- #
APP_TITLE = APP_BASENAME
LAUNCHER_FABRIC = "fabric"
LAUNCHER_NEOFORGE = "neoforge"
LATEST_VERSION = "latest"
GUI_FONT = "Segoe UI Variable Text"
GUI_FONT_SEMIBOLD = "Segoe UI Semibold"
GUI_MESSAGEBOX_TOPMOST = True
DARK_PALETTE = {
    "bg": "#0b1220",
    "surface": "#111a2b",
    "surface_alt": "#162235",
    "border": "#24344f",
    "text": "#ecf3ff",
    "muted": "#9cb0ce",
    "accent": "#58c4ff",
    "accent_dark": "#153756",
    "success": "#43d18d",
    "success_dark": "#153b2c",
    "error": "#ff6b81",
    "error_dark": "#3d1f2b",
    "warning": "#ffd166",
    "log_bg": "#09111d",
    "button": "#2a85ff",
    "button_hover": "#4a98ff",
    "button_alt": "#1c2a42",
    "button_alt_hover": "#263a5c",
    "button_disabled": "#273246",
    "button_disabled_text": "#7f90ae",
    "magenta": "#ff8ad8",
}
LIGHT_PALETTE = {
    "bg": "#eef3f9",
    "surface": "#ffffff",
    "surface_alt": "#e8eef7",
    "border": "#bdc9da",
    "text": "#152238",
    "muted": "#526783",
    "accent": "#168be0",
    "accent_dark": "#c5e4f8",
    "success": "#138a57",
    "success_dark": "#ccebdc",
    "error": "#cf3652",
    "error_dark": "#f4d4da",
    "warning": "#a86c00",
    "log_bg": "#f5f8fc",
    "button": "#187fe0",
    "button_hover": "#3292eb",
    "button_alt": "#dbe5f2",
    "button_alt_hover": "#cbd9e9",
    "button_disabled": "#d6deea",
    "button_disabled_text": "#718097",
    "magenta": "#c7469f",
}
PALETTE = dict(DARK_PALETTE)


def set_color_theme(dark: bool) -> None:
    PALETTE.clear()
    PALETTE.update(DARK_PALETTE if dark else LIGHT_PALETTE)


def get_modpack_catalog_url() -> str:
    return MODPACK_CATALOG_URL




def get_fabric_installer_name(installer_version: str) -> str:
    return f"fabric-installer-{installer_version}.jar"


def get_fabric_installer_url(installer_version: str) -> str:
    name = get_fabric_installer_name(installer_version)
    return f"{FABRIC_MAVEN_URL}/{installer_version}/{name}"


def get_neoforge_installer_name(version: str) -> str:
    return f"neoforge-{version}-installer.jar"


def get_neoforge_installer_url(version: str) -> str:
    return f"{NEOFORGE_MAVEN_URL}/{version}/{get_neoforge_installer_name(version)}"


def get_neoforge_version_prefix(mc_version: str) -> str:
    if prefix := NEOFORGE_VERSION_PREFIX_BY_MC.get(mc_version):
        return prefix
    parts = mc_version.split(".")
    if len(parts) >= 2 and all(part.isdigit() for part in parts):
        if parts[0] == "1":
            return f"{parts[1]}.{parts[2] if len(parts) > 2 else '0'}."
        return f"{parts[0]}.{parts[1]}."
    raise RuntimeError(f"Version Minecraft invalide pour NeoForge: {mc_version}")


def get_adoptium_installer_url(major: int) -> str:
    return (
        f"{ADOPTIUM_API_URL.rsplit('/assets/latest', 1)[0]}/installer/latest/{major}/ga/windows/"
        "x64/jdk/hotspot/normal/eclipse?project=jdk"
    )


def get_java_msi_name(major: int = JAVA_MAJOR) -> str:
    return f"OpenJDK{major}U-jdk_x64_windows_hotspot_latest.msi"


def release_exe_name() -> str:
    return f"{APP_BASENAME}.exe"


def pending_update_name() -> str:
    return f"{APP_BASENAME}{PENDING_UPDATE_SUFFIX}"


def get_minecraft_dir() -> Path:
    appdata = os.getenv("APPDATA")
    if not appdata:
        raise RuntimeError("APPDATA introuvable. Ce script doit être lancé sur Windows.")

    mc_dir = Path(appdata) / MINECRAFT_DIR_NAME
    if not mc_dir.exists():
        raise RuntimeError(
            f"Dossier Minecraft introuvable : {mc_dir}\n"
            "Le launcher Minecraft officiel doit avoir été lancé au moins une fois."
        )

    return mc_dir


def get_installation_dir(name: str) -> Path:
    return get_minecraft_dir() / INSTALLATIONS_DIR_NAME / name


def get_install_subdir(name: str, subdir: str) -> Path:
    return get_installation_dir(name) / subdir


def get_launcher_profiles_path() -> Path:
    return get_minecraft_dir() / LAUNCHER_PROFILES_FILE

# ----- Assets ----- #
ICON = "data:image/png;base64,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"
