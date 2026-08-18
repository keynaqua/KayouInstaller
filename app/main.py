import ctypes
import sys
from pathlib import Path

import logger
from gui import log_queue, show_error_dialog, start_gui
from logger import error
from modpack import ModpackInfo, modpack_info_from_catalog
from pipeline import InstallationPipeline
from uninstall import uninstall_modpack
from utils.updater import check_for_updates, cleanup_other_versions, handle_cleanup_args


class InstallerError(Exception):
    pass


logger.log_queue = log_queue


def is_admin() -> bool:
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def relaunch_as_admin() -> bool:
    if is_admin():
        return True

    exe_or_script = str(Path(sys.argv[0]).resolve())
    params = " ".join(f'"{arg}"' for arg in sys.argv[1:])

    if getattr(sys, "frozen", False):
        executable = exe_or_script
        arguments = params
    else:
        executable = sys.executable
        arguments = f'"{exe_or_script}" {params}'.strip()

    rc = ctypes.windll.shell32.ShellExecuteW(None, "runas", executable, arguments, None, 1)
    if rc <= 32:
        raise RuntimeError("Impossible de demander l'elevation administrateur.")

    return False


def run(info: ModpackInfo, options: dict):
    InstallationPipeline(info, options).run()


def run_modpack(modpack, options: dict | None = None):
    info = modpack_info_from_catalog(modpack)
    if not info.launcher:
        raise InstallerError(f"Le modpack '{info.name}' n'a pas de lanceur configure.")

    run(info, options or {})


def main():
    try:
        handle_cleanup_args()
        cleanup_other_versions()

        if check_for_updates():
            return 0

        if not relaunch_as_admin():
            return 0

        start_gui(run_modpack, uninstall_modpack)
        return 1

    except InstallerError as exc:
        show_error_dialog("Installation echouee", str(exc))
        return 1

    except Exception as exc:
        error("Erreur inattendue")
        show_error_dialog("Erreur inattendue", str(exc))
        return 1


if __name__ == "__main__":
    sys.exit(main())
