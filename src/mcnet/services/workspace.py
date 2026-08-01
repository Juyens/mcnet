import shutil
from pathlib import Path

from mcnet.domain.models import AnyManifest
from mcnet.errors import McnetError
from mcnet.storage import manifest, paths


def available_path(name: str, *, root: Path | None = None) -> Path:
    target = paths.available(name, root=root)

    if target is None:
        raise McnetError(
            f"there is already a folder named '{name}' here",
            hint="check the name, or cd into the folder that contains it",
        )

    return target


def locate(name: str, root: Path | None = None) -> Path:
    return manifest.server_folder(name, root)


def create(target: Path, any_manifest: AnyManifest) -> Path:
    target.mkdir(parents=True)
    return manifest.save_manifest(any_manifest, target)


def forget(folder: Path) -> Path:
    """Drop the manifest, leaving every other file in place."""
    return manifest.remove_manifest(folder)


def delete(folder: Path) -> None:
    shutil.rmtree(folder)


def declared_plugins(folder: Path) -> int:
    return len(manifest.load_manifest(folder).plugins)
