from pathlib import Path

from mcnet.domain.models import LockedJar
from mcnet.errors import McnetError
from mcnet.progress import ProgressTask
from mcnet.providers.protocols import Downloader

PLUGINS_DIR = "plugins"


def plugin_path(folder: Path, entry: LockedJar) -> Path:
    """Where a locked plugin belongs, for servers and proxies alike."""
    return folder / PLUGINS_DIR / entry.filename


def server_path(folder: Path, entry: LockedJar) -> Path:
    """The server or proxy jar sits at the root, next to its manifest."""
    return folder / entry.filename


def install(
    downloader: Downloader,
    path: Path,
    entry: LockedJar,
    task: ProgressTask | None = None,
) -> bool:
    """Put the jar where it belongs. False if it was already there and correct."""
    return downloader.download(
        entry.url,
        path,
        expected=entry.hash,
        algorithm=entry.algorithm,
        task=task,
    )


def uninstall(path: Path) -> bool:
    """Take a jar off disk. False if it was not there."""
    if not path.exists():
        return False

    try:
        path.unlink()
    except OSError as e:
        raise McnetError(
            f"could not delete {path.name}: {e.strerror or e}",
            hint="stop the server if it is running",
        ) from e

    return True
