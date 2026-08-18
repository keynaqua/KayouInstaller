from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from config import (
    CONFIG_DIR_NAME,
    DATAPACKS_DIR_NAME,
    LAUNCHER_FABRIC,
    LAUNCHER_NEOFORGE,
    MODS_DIR_NAME,
    RESOURCEPACKS_DIR_NAME,
    SHADERPACKS_DIR_NAME,
)
from config_sync import load_config_manifest, sync_config_folder
from datapacks import deploy_datapacks, load_datapack_manifest, update_datapacks
from fabric import ensure_fabric_installed
from inventory import Inventory
from java import ensure_java_installed
from logger import download, progress, stage, stage_done, stage_skipped, step, total_size
from minecraft import create_minecraft_profile
from minecraft.worlds import create_world
from modpack import ModpackInfo
from mods import load_mod_manifest, update_mods
from neoforge import ensure_neoforge_installed
from shaders import activate_shader, ensure_shaders_installed, load_shaderpack_manifest
from resourcepacks import activate_resourcepacks, load_resourcepack_manifest, update_resourcepacks


@dataclass(frozen=True)
class PipelineStage:
    key: str
    label: str
    progress: int
    action: Callable[[], None]


class InstallationPipeline:
    def __init__(self, info: ModpackInfo, options: dict | None = None):
        self.info = info
        self.options = options or {}
        self.safe_mode = self.options.get("safe_mode") is True
        self.game_dir: Path | None = None
        self.version_id: str | None = None
        self.java_command: str | None = None
        self.inventory: Inventory | None = None
        self.mod_manifest = None
        self.resourcepack_manifest = None
        self.shaderpack_manifest = None
        self.config_manifest = None
        self.datapack_manifest = None
        self.counts = {}
        self.skipped_stages = {}
        self.progress_ranges = {
            "validate": (1, 4), "java": (4, 8), "loader": (8, 12),
            "profile": (12, 15), "mods": (15, 70), "resourcepacks": (70, 80),
            "shaders": (80, 90), "datapacks": (90, 94), "configs": (94, 97),
            "activate": (97, 99),
        }

    def run(self) -> None:
        for item in self.stages():
            start, end = self.progress_ranges[item.key]
            progress(start)
            stage(item.key, item.label)
            step(item.label)
            item.action()
            progress(end)
            if item.key in self.skipped_stages:
                stage_skipped(item.key, self.skipped_stages[item.key])
            else:
                stage_done(item.key, self._summary(item.key))
        self._inventory().set_revision(str(self.options.get("revision", "")))
        size = sum(path.stat().st_size for value in self._inventory().all_files() if (path := self._path() / value).is_file())
        self._inventory().set_size_bytes(size)
        total_size(size)
        progress(100)
        step("Installation terminee !")

    def _summary(self, key: str) -> str:
        labels = {
            "validate": "Manifestes validés",
            "java": "Java installé et prêt",
            "loader": f"{self.info.launcher.title()} installé",
            "profile": "Profil Minecraft créé",
            "activate": "Packs activés",
        }
        if key in self.counts:
            done, total, label = self.counts[key]
            return f"{label} installés ({done}/{total})"
        return labels.get(key, key.title())

    def stages(self) -> tuple[PipelineStage, ...]:
        return (
            PipelineStage("validate", "Validation des manifests...", 1, self._validate),
            PipelineStage("java", "Vérification de Java...", 4, self._java),
            PipelineStage("loader", f"Vérification de {self.info.launcher.title()}...", 8, self._loader),
            PipelineStage("profile", "Préparation du profil Minecraft...", 12, self._profile),
            PipelineStage("mods", "Synchronisation des mods...", 15, self._mods),
            PipelineStage("resourcepacks", "Synchronisation des packs de ressources...", 70, self._resourcepacks),
            PipelineStage("shaders", "Synchronisation des shaders...", 80, self._shaders),
            PipelineStage("datapacks", "Synchronisation des datapacks...", 90, self._datapacks),
            PipelineStage("configs", "Synchronisation des configs...", 94, self._configs),
            PipelineStage("activate", "Activation des packs...", 97, self._activate),
        )

    def _validate(self) -> None:
        cache_version = str(self.options.get("revision", ""))
        self.mod_manifest = load_mod_manifest(self.info.manifest_url("mods"), cache_version)
        self.resourcepack_manifest = load_resourcepack_manifest(self.info.manifest_url("resourcepacks"), cache_version)
        self.shaderpack_manifest = load_shaderpack_manifest(self.info.manifest_url("shaderpacks"), cache_version)
        self.datapack_manifest = load_datapack_manifest(self.info.manifest_url("datapacks"), cache_version)
        self.config_manifest = load_config_manifest(self.info.manifest_url("configs", required=False), cache_version)
        self._build_progress_ranges()

    def _build_progress_ranges(self) -> None:
        item_counts = {
            "mods": len(self.mod_manifest[0]) if self.mod_manifest else 0,
            "resourcepacks": len(self.resourcepack_manifest or []),
            "shaders": len(self.shaderpack_manifest or []),
            "datapacks": len(self.datapack_manifest or []),
            "configs": len(self.config_manifest.files) if self.config_manifest else 0,
        }
        units = {key: max(1, count) for key, count in item_counts.items()}
        total_units = sum(units.values())
        cursor = 15
        keys = tuple(units)
        cumulative = 0
        for index, key in enumerate(keys):
            cumulative += units[key]
            end = 97 if index == len(keys) - 1 else 15 + 2 * (index + 1) + round(72 * cumulative / total_units)
            end = max(cursor + 1, min(97, end))
            self.progress_ranges[key] = (cursor, end)
            cursor = end

    def _mapped_progress(self, key: str, source_start: int, source_end: int):
        target_start, target_end = self.progress_ranges[key]
        source_span = max(1, source_end - source_start)

        def callback(value: int) -> None:
            ratio = max(0.0, min(1.0, (value - source_start) / source_span))
            progress(round(target_start + ratio * (target_end - target_start)))

        return callback

    def _java(self) -> None:
        self.java_command = ensure_java_installed(self.info.java_version, download)

    def _loader(self) -> None:
        loaders = {
            LAUNCHER_FABRIC: ensure_fabric_installed,
            LAUNCHER_NEOFORGE: ensure_neoforge_installed,
        }
        try:
            install = loaders[self.info.launcher]
        except KeyError as exc:
            raise RuntimeError(f"Lanceur inconnu: {self.info.launcher}") from exc
        self.version_id = install(
            self.info.minecraft_version,
            self.info.launcher_version,
            download,
            self.java_command or "java",
        )

    def _profile(self) -> None:
        if not self.version_id:
            raise RuntimeError("Loader non prepare")
        self.game_dir = create_minecraft_profile(
            self.info.name,
            self.info.installation_dir,
            self.version_id,
            self.info.logo_url,
            int(self.options.get("ram_gb", 4)),
        )
        self.inventory = Inventory(self.game_dir, self.info.key)
        self.inventory.set_installed(True)

    def _mods(self) -> None:
        files = update_mods(
            self._path() / MODS_DIR_NAME,
            self.info.key,
            safe_mode=self.safe_mode,
            progress_callback=self._mapped_progress("mods", 30, 70),
            download_callback=download,
            manifest=self.mod_manifest,
        )
        self._record("mods", MODS_DIR_NAME, files)
        expected = len(self.mod_manifest[0]) if self.mod_manifest else 0
        self.counts["mods"] = (len(files), expected, "Mods")

    def _resourcepacks(self) -> None:
        files = update_resourcepacks(
            self._path(),
            self.info.key,
            progress_callback=self._mapped_progress("resourcepacks", 70, 80),
            download_callback=download,
            manifest=self.resourcepack_manifest,
        )
        self._record("resourcepacks", RESOURCEPACKS_DIR_NAME, files)
        self.counts["resourcepacks"] = (len(files), len(self.resourcepack_manifest or []), "Packs de ressources")

    def _shaders(self) -> None:
        files = ensure_shaders_installed(
            self._path(),
            self.info.key,
            progress_callback=self._mapped_progress("shaders", 80, 90),
            download_callback=download,
            manifest=self.shaderpack_manifest,
        )
        self._record("shaderpacks", SHADERPACKS_DIR_NAME, files)
        self.counts["shaders"] = (len(files), len(self.shaderpack_manifest or []), "Shaders")

    def _datapacks(self) -> None:
        world = self.options.get("datapack_world")
        if not world:
            self._inventory().sync("datapacks", [])
            self._inventory().sync("deployed_datapacks", [])
            self.counts["datapacks"] = (0, 0, "Datapacks")
            self.skipped_stages["datapacks"] = "Datapacks ignorés — aucun monde sélectionné"
            return
        files = update_datapacks(
            self._path(),
            self.info.key,
            progress_callback=self._mapped_progress("datapacks", 90, 94),
            download_callback=download,
            manifest=self.datapack_manifest,
        )
        self._record("datapacks", DATAPACKS_DIR_NAME, files)
        self.counts["datapacks"] = (len(files), len(self.datapack_manifest or []), "Datapacks")
        if world and not (self._path() / "saves" / world / "level.dat").is_file():
            create_world(self._path(), world, world, self.info.minecraft_version)
        available = set(files)
        packs = [pack for pack in self.datapack_manifest or [] if pack.file_name in available]
        deployed = deploy_datapacks(self._path(), packs, [world]) if world else []
        self._inventory().sync("deployed_datapacks", deployed)

    def _configs(self) -> None:
        if self.config_manifest is None and self._inventory().has_category("configs"):
            return
        result = sync_config_folder(
            self.info.installation_dir,
            CONFIG_DIR_NAME,
            download_callback=download,
            manifest=self.config_manifest,
        )
        self._inventory().sync("configs", result.files, remove_stale=False)
        self._inventory().sync("managed_configs", result.managed)
        expected = len(self.config_manifest.files) if self.config_manifest else len(result.files)
        self.counts["configs"] = (len(result.files), expected, "Configs")

    def _activate(self) -> None:
        activate_resourcepacks(
            self._path(),
            self.resourcepack_manifest or [],
            self.options.get("activate_resourcepacks", True) is True,
        )
        if self.shaderpack_manifest:
            activate_shader(
                self._path(),
                self.shaderpack_manifest,
                self.options.get("activate_shader", True) is True,
            )

    def _record(self, category: str, directory: str, files: list[str]) -> None:
        paths = [(Path(directory) / name).as_posix() for name in files]
        self._inventory().sync(category, paths)

    def _path(self) -> Path:
        if self.game_dir is None:
            raise RuntimeError("Profil Minecraft non prepare")
        return self.game_dir

    def _inventory(self) -> Inventory:
        if self.inventory is None:
            raise RuntimeError("Inventaire non prepare")
        return self.inventory
