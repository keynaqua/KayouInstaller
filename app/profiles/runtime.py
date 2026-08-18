from __future__ import annotations

from dataclasses import dataclass

from utils.files import validate_format
from utils.http import get_json


@dataclass(frozen=True)
class VisualProfile:
    id: str
    name: str
    logo: str = ""
    resourcepacks: tuple[str, ...] = ()
    shader: str = ""


@dataclass(frozen=True)
class ProfileManifest:
    default: str
    profiles: tuple[VisualProfile, ...]

    def get(self, profile_id: str) -> VisualProfile | None:
        return next((profile for profile in self.profiles if profile.id == profile_id), None)


def load_profile_manifest(manifest_url: str, cache_version: str = "") -> ProfileManifest:
    if not manifest_url:
        return ProfileManifest("", ())
    data = get_json(manifest_url, cache_key=cache_version)
    if not isinstance(data, dict):
        raise RuntimeError("profiles.json doit être un objet JSON")
    validate_format(data, "profiles.json")
    raw = data.get("profiles")
    if not isinstance(raw, list) or not raw:
        raise RuntimeError("profiles.json: profiles doit être une liste non vide")
    profiles = []
    ids = set()
    for index, entry in enumerate(raw, start=1):
        if not isinstance(entry, dict):
            raise RuntimeError(f"profiles.json: profiles[{index}] invalide")
        profile_id = str(entry.get("id", "")).strip()
        name = str(entry.get("name", "")).strip()
        packs = entry.get("resourcepacks", [])
        if not profile_id or not name or not isinstance(packs, list):
            raise RuntimeError(f"profiles.json: profiles[{index}] incomplet")
        if profile_id in ids:
            raise RuntimeError(f"profiles.json: id dupliqué '{profile_id}'")
        ids.add(profile_id)
        profiles.append(VisualProfile(
            id=profile_id,
            name=name,
            logo=str(entry.get("logo", "")).strip(),
            resourcepacks=tuple(value.strip() for value in packs if isinstance(value, str) and value.strip()),
            shader=str(entry.get("shader", "")).strip(),
        ))
    default = str(data.get("default", profiles[0].id)).strip()
    if default not in ids:
        raise RuntimeError("profiles.json: profil par défaut inconnu")
    return ProfileManifest(default, tuple(profiles))
