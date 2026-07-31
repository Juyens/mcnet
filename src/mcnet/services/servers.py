import shutil
from dataclasses import dataclass, field
from pathlib import Path

from mcnet.domain.models import Manifest
from mcnet.errors import McnetError
from mcnet.storage import manifest, paths

WORLD_NAME = "world"


@dataclass(frozen=True)
class FieldChange:
    label: str
    old: object
    new: object


@dataclass
class Edit:
    applied: list[FieldChange] = field(default_factory=list)
    unchanged: list[FieldChange] = field(default_factory=list)
    needs_sync: bool = False

    def record(self, label: str, old: object, new: object) -> bool:
        """True when new differs from old, filing the change either way."""
        if old == new:
            self.unchanged.append(FieldChange(label, old, new))
            return False

        self.applied.append(FieldChange(label, old, new))
        return True


def locate(name: str, root: Path | None = None) -> Path:
    return manifest.server_folder(name, root)


def create(
    name: str,
    *,
    loader: str,
    mc_version: str,
    port: int,
    root: Path | None = None,
) -> Path:
    """Make the folder and its manifest, returning the path of the manifest."""
    target = (root or Path.cwd()) / name

    if target.exists():
        raise McnetError(
            f"{paths.display(target)} already exists",
            hint="pick another name, or remove the folder first",
        )

    target.mkdir(parents=True)

    server = Manifest(loader=loader, mc_version=mc_version, port=port, plugins=[])

    return manifest.save_manifest(server, target)


def edit(
    folder: Path,
    *,
    loader: str | None = None,
    mc_version: str | None = None,
    port: int | None = None,
) -> Edit:
    """Apply the settings that differ, saving only if something changed."""
    server = manifest.load_manifest(folder)
    result = Edit()

    if loader is not None and result.record("loader", server.loader, loader):
        server.loader = loader
        result.needs_sync = True

    if mc_version is not None and result.record(
        "version", server.mc_version, mc_version
    ):
        server.mc_version = mc_version
        result.needs_sync = True

    if port is not None and result.record("port", server.port, port):
        server.port = port

    if result.applied:
        manifest.save_manifest(server, folder)

    return result


def forget(folder: Path) -> Path:
    """Drop the manifest, leaving every other file in place."""
    return manifest.remove_manifest(folder)


def delete(folder: Path) -> None:
    shutil.rmtree(folder)


def declared_plugins(folder: Path) -> int:
    return len(manifest.load_manifest(folder).plugins)


def has_world(folder: Path) -> bool:
    return (folder / WORLD_NAME).exists()
