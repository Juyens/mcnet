import os
import sys
from pathlib import Path

from mcnet.providers.http import Http

USER_AGENT = "juyens/mcnet (joseph.juliuscb@gmail.com)"


_http: Http | None = None


def cache_dir() -> Path:
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData/Local"))
    else:
        base = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
    return base / "mcnet"


def get_http() -> Http:
    global _http
    if _http is None:
        _http = Http(USER_AGENT, cache_dir())
    return _http
