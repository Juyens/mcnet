import shutil
from pathlib import Path

from mcnet.domain.changes import ChangeSet
from mcnet.domain.loaders import ProxyLoader
from mcnet.errors import McnetError
from mcnet.storage import discovery, manifest
from mcnet.storage.manifest import ProxyManifest, ServerManifest

WORLD_NAME = "world"


def create(
    name: str,
    *,
    loader: str,
    mc_version: str,
    port: int,
    root: Path | None = None,
) -> Path:
    """Make the folder and its manifest, returning the path of the manifest."""
    target = available_path(name, root=root)

    if loader in ProxyLoader:
        target_manifest = ProxyManifest(loader=loader, mc_version=mc_version, port=port)
    else:
        target_manifest = ServerManifest(
            loader=loader, mc_version=mc_version, port=port
        )

    target.mkdir(parents=True)

    return manifest.save_manifest(target_manifest, target)


def edit(
    folder: Path,
    *,
    loader: str | None = None,
    mc_version: str | None = None,
    port: int | None = None,
) -> ChangeSet:
    """Apply the settings that differ, saving only if something changed."""
    server = manifest.load_server(folder)
    changes = ChangeSet()

    if loader is not None and changes.record(
        "loader", server.loader, loader, syncs=True
    ):
        server.loader = loader

    if mc_version is not None and changes.record(
        "version", server.mc_version, mc_version, syncs=True
    ):
        server.mc_version = mc_version

    if port is not None and changes.record("port", server.port, port):
        server.port = port

    if changes.applied:
        manifest.save_manifest(server, folder)

    return changes


def has_world(folder: Path) -> bool:
    return (folder / WORLD_NAME).exists()


def available_path(name: str, *, root: Path | None = None) -> Path:
    target = discovery.available(name, root=root)

    if target is None:
        raise McnetError(
            f"there is already a folder named '{name}' here",
            hint="check the name, or cd into the folder that contains it",
        )

    return target


def locate(name: str, root: Path | None = None) -> Path:
    return discovery.locate(name, root)


def forget(folder: Path) -> Path:
    """Drop the manifest, leaving every other file in place."""
    return manifest.remove_manifest(folder)


def delete(folder: Path) -> None:
    shutil.rmtree(folder)


def declared_plugins(folder: Path) -> int:
    return len(manifest.load_manifest(folder).plugins)
