import shutil
from pathlib import Path

from mcnet.domain import loaders
from mcnet.domain.changes import ChangeSet
from mcnet.domain.models import Target
from mcnet.errors import McnetError
from mcnet.storage import discovery, lock, manifest
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

    if loaders.is_proxy(loader):
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


def named(names: list[str], root: Path | None = None) -> tuple[list[Target], list[str]]:
    """Targets for the names that exist here, and the names that do not.

    A typo in the fifth name should not cancel the other four, so the misses
    come back to be reported rather than raised.
    """
    targets, unknown = [], []

    for name in names:
        folder = discovery.find(name, root)

        if folder is None:
            unknown.append(name)
        else:
            targets.append(Target(name, folder))

    return targets, unknown


def here(root: Path | None = None) -> Target | None:
    """The server we are standing in, if we are standing in one."""
    folder = discovery.current(root)

    if folder is None:
        return None

    return Target(folder.name, folder)


def everything(root: Path | None = None) -> list[Target]:
    """Every server managed under root, in name order."""
    return [Target(folder.name, folder) for folder in discovery.managed(root)]


def forget(folder: Path) -> Path:
    """Drop the manifest and its lock, leaving every other file in place."""
    lock.remove_lock(folder)

    return manifest.remove_manifest(folder)


def delete(folder: Path) -> None:
    shutil.rmtree(folder)


def declared_plugins(folder: Path) -> int:
    return len(manifest.load_manifest(folder).plugins)
