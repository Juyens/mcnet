import re
from pathlib import Path

PROPERTIES_NAME = "server.properties"

VELOCITY_NAME = "velocity.toml"

BIND_KEY = "bind"

ANY_HOST = "0.0.0.0"


def set_port(folder: Path, port: int, *, proxy: bool) -> Path:
    """Put the declared port where that kind of server reads it from."""
    if proxy:
        return _set_toml(folder / VELOCITY_NAME, BIND_KEY, f'"{ANY_HOST}:{port}"')

    return _set_property(folder / PROPERTIES_NAME, "server-port", str(port))


def _set_property(path: Path, key: str, value: str) -> Path:
    """Set one key, leaving every other line, comment and order untouched.

    A file with a single key is legal: the server fills in what it does not
    find and writes the rest back on its first start, so mcnet only ever has
    to state what the manifest declares.
    """
    return _rewrite(path, re.compile(rf"^\s*{re.escape(key)}\s*="), f"{key}={value}")


def _set_toml(path: Path, key: str, rendered: str) -> Path:
    """Set one top-level scalar. Nested tables would need a real TOML writer."""
    return _rewrite(
        path, re.compile(rf"^\s*{re.escape(key)}\s*="), f"{key} = {rendered}"
    )


def _rewrite(path: Path, matches: re.Pattern[str], line: str) -> Path:
    lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    replaced = False

    for index, existing in enumerate(lines):
        if matches.match(existing):
            lines[index] = line
            replaced = True
            break

    if not replaced:
        lines.append(line)

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    return path
