import os
import sys
from pathlib import Path


def cache_dir() -> Path:
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData/Local"))
    else:
        base = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
    return base / "mcnet"


def display(path: Path) -> str:
    """Path relative to the current folder when possible, absolute otherwise."""
    try:
        return str(path.relative_to(Path.cwd()))
    except ValueError:
        return str(path)
