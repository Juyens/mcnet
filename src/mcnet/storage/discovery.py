from pathlib import Path

from mcnet.errors import McnetError
from mcnet.storage.manifest import MANIFEST_NAME


def available(name: str, root: Path | None = None) -> Path | None:
    """Path for a new folder under root, or None if something is already there."""
    target = (root or Path.cwd()) / name

    if target.exists():
        return None

    return target


def find(name: str, root: Path | None = None) -> Path | None:
    """Folder of a managed server or proxy under root, or None."""
    folder = (root or Path.cwd()) / name

    if not (folder / MANIFEST_NAME).exists():
        return None

    return folder


def current(root: Path | None = None) -> Path | None:
    """The folder itself when it is a managed server, not one of its children.

    Standing inside a server and asking for work should mean that server.
    """
    base = root or Path.cwd()

    if not (base / MANIFEST_NAME).exists():
        return None

    return base


def managed(root: Path | None = None) -> list[Path]:
    """Every folder under root that mcnet manages, in name order.

    Sorted so a sync over a network reports its servers the same way twice.
    """
    base = root or Path.cwd()

    if not base.is_dir():
        return []

    folders = []

    for entry in sorted(base.iterdir()):
        if entry.is_dir() and (entry / MANIFEST_NAME).exists():
            folders.append(entry)

    return folders


def locate(name: str, root: Path | None = None) -> Path:
    """Same as find, but fails when there is nothing there."""
    folder = find(name, root)

    if folder is None:
        raise McnetError(
            f"nothing named '{name}' is managed here",
            hint="check the name, or cd into the folder that contains it",
        )

    return folder
