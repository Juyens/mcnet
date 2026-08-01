from pathlib import Path

from mcnet.domain.changes import ChangeSet
from mcnet.domain.models import ProxyManifest
from mcnet.services import workspace
from mcnet.services.workspace import declared_plugins, delete, forget, locate
from mcnet.storage import manifest

__all__ = ["create", "declared_plugins", "delete", "edit", "forget", "locate"]


def create(name: str, *, loader: str, port: int, root: Path | None = None) -> Path:
    """Make the folder and its manifest, returning the path of the manifest."""
    target = workspace.available_path(name, root=root)
    proxy = ProxyManifest(loader=loader, port=port)
    return workspace.create(target, proxy)


def edit(
    folder: Path,
    *,
    loader: str | None = None,
    port: int | None = None,
) -> ChangeSet:
    """Apply the settings that differ, saving only if something changed."""
    proxy = manifest.load_proxy(folder)
    changes = ChangeSet()

    if loader is not None and changes.record(
        "loader", proxy.loader, loader, syncs=True
    ):
        proxy.loader = loader

    if port is not None and changes.record("port", proxy.port, port):
        proxy.port = port

    if changes.applied:
        manifest.save_manifest(proxy, folder)

    return changes
