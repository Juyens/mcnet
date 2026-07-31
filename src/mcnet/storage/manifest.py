from pathlib import Path

import yaml

from mcnet.domain.models import Manifest
from mcnet.errors import McnetError
from mcnet.storage import paths, schema

MANIFEST_NAME = "mcnet.yaml"

_IGNORED = frozenset({".git", ".venv", "node_modules", "__pycache__"})


def find_server(name: str, root: Path | None = None) -> Path | None:
    """Folder of a named server under root, or None if there is none."""
    folder = (root or Path.cwd()) / name

    if not (folder / MANIFEST_NAME).exists():
        return None

    return folder


def server_folder(name: str, root: Path | None = None) -> Path:
    folder = find_server(name, root)

    if folder is None:
        raise McnetError(
            f"no server named '{name}' here",
            hint="check the name, or cd into the folder that contains it",
        )

    return folder


def save_manifest(manifest: Manifest, folder: Path) -> Path:
    path = folder / MANIFEST_NAME
    path.write_text(
        yaml.safe_dump(schema.to_dict(manifest), sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )

    return path


def load_manifest(folder: Path) -> Manifest:
    path = folder / MANIFEST_NAME

    if not path.exists():
        raise McnetError(f"no {MANIFEST_NAME} in {paths.display(folder)}")

    raw = yaml.safe_load(path.read_text(encoding="utf-8"))

    if not isinstance(raw, dict):
        raise McnetError(f"{paths.display(path)} is not a mcnet manifest")

    return schema.from_dict(raw, path)


def remove_manifest(folder: Path) -> Path:
    path = folder / MANIFEST_NAME
    path.unlink()

    return path
