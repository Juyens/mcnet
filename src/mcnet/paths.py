import os
import sys
from pathlib import Path

APP_NAME = "mcnet"


def cache_dir() -> Path:
    """Where mcnet keeps what it can fetch again on this machine."""
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData/Local"))
    else:
        base = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))

    return base / APP_NAME
