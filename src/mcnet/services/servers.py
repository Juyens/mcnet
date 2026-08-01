from pathlib import Path

from mcnet.domain.changes import ChangeSet
from mcnet.domain.models import ServerManifest
from mcnet.services import workspace
from mcnet.services.workspace import declared_plugins, delete, forget, locate
from mcnet.storage import manifest

__all__ = ["create", "declared_plugins", "delete", "edit", "forget", "locate"]

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
    target = workspace.available_path(name, root=root)
    server = ServerManifest(loader=loader, mc_version=mc_version, port=port, plugins=[])
    return workspace.create(target, server)


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
