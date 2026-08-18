import ctypes
import os
import shutil
import subprocess
import tempfile
import winreg
from pathlib import Path

from config import (
    JAVA_BIN_DIR_NAME,
    JAVA_COMMAND,
    JAVA_DEFAULT_ROOT,
    JAVA_EXE_NAME,
    JAVA_MAJOR,
    LOG_SUFFIX,
    MSI_SUFFIX,
    get_adoptium_installer_url,
    get_java_msi_name,
)
from logger import info, success
from utils.http import download_file
from utils.files import FileProgressCallback, bind_progress
from utils.process import get_command_output
from utils.version import parse_java_major


def get_java_major(java_cmd: str = JAVA_COMMAND) -> int | None:
    try:
        return parse_java_major(get_command_output([java_cmd, "-version"]))
    except OSError:
        return None


def is_java_ok(major: int = JAVA_MAJOR) -> bool:
    java_path = shutil.which(JAVA_COMMAND)
    return bool(java_path and get_java_major(java_path) == major)


def find_java_executable(major: int = JAVA_MAJOR) -> Path | None:
    command = shutil.which(JAVA_COMMAND)
    if command and get_java_major(command) == major:
        return Path(command)
    java_bin = find_java_bin_default(major)
    return java_bin / JAVA_EXE_NAME if java_bin else None


def find_java_bin_default(major: int = JAVA_MAJOR) -> Path | None:
    if not JAVA_DEFAULT_ROOT.exists():
        return None

    for child in sorted(JAVA_DEFAULT_ROOT.iterdir(), reverse=True):
        java_exe = child / JAVA_BIN_DIR_NAME / JAVA_EXE_NAME
        if java_exe.exists() and get_java_major(str(java_exe)) == major:
            return java_exe.parent
    return None


def add_directory_to_user_path(directory: Path) -> None:
    directory_str = str(directory)
    with winreg.OpenKey(
        winreg.HKEY_CURRENT_USER,
        "Environment",
        0,
        winreg.KEY_READ | winreg.KEY_WRITE,
    ) as key:
        try:
            current_path, _ = winreg.QueryValueEx(key, "Path")
        except FileNotFoundError:
            current_path = ""

        entries = [entry.strip().lower() for entry in current_path.split(";") if entry.strip()]
        if directory_str.lower() not in entries:
            winreg.SetValueEx(
                key,
                "Path",
                0,
                winreg.REG_EXPAND_SZ,
                current_path + (";" if current_path else "") + directory_str,
            )

    os.environ["PATH"] = directory_str + os.pathsep + os.environ.get("PATH", "")


def download_java_msi(
    major: int = JAVA_MAJOR,
    callback: FileProgressCallback | None = None,
) -> Path:
    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=MSI_SUFFIX)
    tmp_file.close()
    info(f"Telechargement de Java {major} ({get_java_msi_name(major)})...")
    return download_file(
        get_adoptium_installer_url(major),
        Path(tmp_file.name),
        callback=bind_progress(get_java_msi_name(major), callback),
    )


def install_java_silently(msi_path: Path) -> None:
    log_file = tempfile.NamedTemporaryFile(delete=False, suffix=LOG_SUFFIX)
    log_file.close()
    log_path = Path(log_file.name)

    info("Installation silencieuse de Java...")
    info(f"Log MSI : {log_path}")
    try:
        result = subprocess.run(
            [
                "msiexec",
                "/i",
                str(msi_path),
                "ADDLOCAL=FeatureMain,FeatureEnvironment,FeatureJarFileRunWith,FeatureJavaHome",
                "/qn",
                "/norestart",
                "/L*v",
                str(log_path),
            ],
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"Echec de l'installation Java (code retour {result.returncode}). "
                f"Consulte le log MSI : {log_path}"
            )
    finally:
        for path in (msi_path, log_path):
            try:
                if path.exists():
                    path.unlink()
            except OSError:
                pass


def is_admin() -> bool:
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def ensure_java_in_path_from_default_install(major: int = JAVA_MAJOR) -> bool:
    java_bin = find_java_bin_default(major)
    if not java_bin:
        return False

    info(f"Java {major} detecte au chemin par defaut : {java_bin}")
    add_directory_to_user_path(java_bin)
    success("Java ajoute au PATH utilisateur.")
    return True


def ensure_java_installed(
    major: int = JAVA_MAJOR,
    download_callback: FileProgressCallback | None = None,
) -> str:
    if java := find_java_executable(major):
        success(f"Java {major} deja installe et disponible dans le PATH.")
        return str(java)

    if ensure_java_in_path_from_default_install(major) and is_java_ok(major):
        success(f"Java {major} est maintenant disponible.")
        return str(find_java_executable(major))

    msi_path = download_java_msi(major, download_callback)
    if not is_admin():
        raise RuntimeError(
            "L'installation de Java necessite des droits administrateur. "
            "Relance le terminal ou l'installeur en tant qu'administrateur."
        )
    install_java_silently(msi_path)

    if is_java_ok(major):
        success(f"Java {major} installe avec succes.")
        return str(find_java_executable(major))

    if ensure_java_in_path_from_default_install(major) and is_java_ok(major):
        success(f"Java {major} installe et ajoute au PATH.")
        return str(find_java_executable(major))

    raise RuntimeError(
        f"Java {major} a ete installe, mais n'est toujours pas detecte correctement."
    )
