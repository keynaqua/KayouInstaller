from dataclasses import dataclass
from config import JAVA_MAJOR
from catalog import CatalogEntry


@dataclass(frozen=True)
class ModpackInfo:
    key: str
    name: str
    minecraft_version: str
    launcher: str
    launcher_version: str
    installation_dir: str
    java_version: int = JAVA_MAJOR
    logo_url: str = ""
    manifest_urls: dict[str, str] | None = None
    resourcepack_activation_ids: tuple[str, ...] = ()

    def manifest_url(self, name: str, required: bool = True) -> str:
        url = (self.manifest_urls or {}).get(name, "")
        if required and not url:
            raise RuntimeError(f"Manifest '{name}' absent pour {self.name}")
        return url


def modpack_info_from_catalog(pack: CatalogEntry) -> ModpackInfo:
    return ModpackInfo(
        key=pack.id,
        name=pack.name,
        minecraft_version=pack.minecraft_version,
        launcher=pack.loader,
        launcher_version=pack.loader_version,
        installation_dir=pack.installation_dir or pack.id,
        java_version=pack.java_version,
        logo_url=pack.logo,
        manifest_urls=pack.manifests or {},
        resourcepack_activation_ids=pack.resourcepack_activation_ids,
    )
