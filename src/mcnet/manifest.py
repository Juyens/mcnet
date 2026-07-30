from pathlib import Path
from typing import Any

import yaml

from mcnet.core import paths
from mcnet.core.error import McnetError
from mcnet.core.models import Manifest, Plugin

MANIFEST_NAME = "mcnet.yaml"
SCHEMA = 1

_IGNORED = frozenset({".git", ".venv", "node_modules", "__pycache__"})


def _require(raw: dict[str, Any], key: str, path: Path) -> Any:
    if key not in raw:
        raise McnetError(f"{paths.display(path)} is missing '{key}'")

    return raw[key]


def server_folder(name: str, root: Path | None = None) -> Path:
    """Folder of a named server under root (default: cwd)."""
    folder = (root or Path.cwd()) / name

    if not (folder / MANIFEST_NAME).exists():
        raise McnetError(
            f"no server named '{name}' here",
            hint="check the name, or cd into the folder that contains it",
        )

    return folder


def save_manifest(manifest: Manifest, folder: Path) -> Path:
    plugins = []
    for plugin in manifest.plugins:
        plugins.append({"source": plugin.source, "slug": plugin.slug})

    data = {
        "schema": SCHEMA,
        "loader": manifest.loader,
        "mc_version": manifest.mc_version,
        "port": manifest.port,
        "plugins": plugins,
    }

    path = folder / MANIFEST_NAME
    path.write_text(
        yaml.safe_dump(data, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )

    return path


def load_manifest(folder: Path) -> Manifest:
    path = folder / MANIFEST_NAME

    if not path.exists():
        raise McnetError(f"no {MANIFEST_NAME} in {paths.display(folder)}")

    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}

    if "schema" not in raw:
        raise McnetError(f"{paths.display(path)} is not a mcnet manifest")

    if raw["schema"] > SCHEMA:
        raise McnetError(
            f"{paths.display(path)} needs a newer mcnet "
            f"(schema {raw['schema']}, this one reads {SCHEMA})"
        )

    plugins = []
    for entry in raw.get("plugins") or []:
        plugins.append(Plugin(source=entry["source"], slug=entry["slug"]))

    return Manifest(
        loader=_require(raw, "loader", path),
        mc_version=_require(raw, "mc_version", path),
        port=_require(raw, "port", path),
        plugins=plugins,
    )


def remove_manifest(folder: Path) -> Path:
    path = folder / MANIFEST_NAME
    path.unlink()

    return path
