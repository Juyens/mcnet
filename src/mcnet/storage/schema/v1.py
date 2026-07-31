from pathlib import Path
from typing import Any

from mcnet.domain.models import Manifest, Plugin
from mcnet.errors import McnetError
from mcnet.storage import paths

VERSION = 1


def to_dict(manifest: Manifest) -> dict[str, Any]:
    plugins = []
    for plugin in manifest.plugins:
        plugins.append({"source": plugin.source, "slug": plugin.slug})

    return {
        "schema": VERSION,
        "loader": manifest.loader,
        "mc_version": manifest.mc_version,
        "port": manifest.port,
        "plugins": plugins,
    }


def from_dict(raw: dict[str, Any], path: Path) -> Manifest:
    return Manifest(
        loader=_require(raw, "loader", path),
        mc_version=_require(raw, "mc_version", path),
        port=_require(raw, "port", path),
        plugins=_plugins(raw, path),
    )


def _require(raw: dict[str, Any], key: str, path: Path) -> Any:
    if key not in raw:
        raise McnetError(f"{paths.display(path)} is missing '{key}'")

    return raw[key]


def _plugins(raw: dict[str, Any], path: Path) -> list[Plugin]:
    plugins = []

    for entry in raw.get("plugins") or []:
        if not isinstance(entry, dict):
            raise McnetError(f"{paths.display(path)} has a malformed plugin entry")

        plugins.append(
            Plugin(
                source=_require(entry, "source", path),
                slug=_require(entry, "slug", path),
            )
        )

    return plugins
