from pathlib import Path

from mcnet.domain.models import LockedJar
from mcnet.errors import McnetError
from mcnet.providers.protocols import Downloader

PLUGINS_DIR = "plugins"


def plugin_path(folder: Path, entry: LockedJar) -> Path:
    """Where a locked plugin belongs, for servers and proxies alike."""
    return folder / PLUGINS_DIR / entry.filename


def install(downloader: Downloader, folder: Path, entry: LockedJar) -> bool:
    """Put the jar in the server's plugins folder. False if it was already there."""
    return downloader.download(
        entry.url,
        plugin_path(folder, entry),
        expected=entry.hash,
        algorithm=entry.algorithm,
    )


def uninstall(folder: Path, entry: LockedJar) -> bool:
    """Take the jar out of the plugins folder. False if it was not there."""
    path = plugin_path(folder, entry)

    if not path.exists():
        return False

    try:
        path.unlink()
    except OSError as e:
        raise McnetError(
            f"could not delete {entry.filename}: {e.strerror or e}",
            hint="stop the server if it is running",
        ) from e

    return True
