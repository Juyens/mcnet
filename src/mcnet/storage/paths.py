import os
import sys
from pathlib import Path


def available(name: str, root: Path | None = None) -> Path | None:
    """Path for a new folder under root. Fails if something is already there."""
    target = (root or Path.cwd()) / name

    if target.exists():
        return None

    return target


def cache_dir() -> Path:
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData/Local"))
    else:
        base = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
    return base / "mcnet"
