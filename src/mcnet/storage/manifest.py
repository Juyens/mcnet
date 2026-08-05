from pathlib import Path

import yaml

from mcnet.domain.models import AnyManifest, ProxyManifest, ServerManifest
from mcnet.errors import McnetError
from mcnet.storage import schema

MANIFEST_NAME = "mcnet.yaml"


def save_manifest(manifest: AnyManifest, folder: Path) -> Path:
    path = folder / MANIFEST_NAME
    path.write_text(
        yaml.safe_dump(
            schema.manifest_to_dict(manifest), sort_keys=False, allow_unicode=True
        ),
        encoding="utf-8",
    )

    return path


def load_manifest(folder: Path) -> AnyManifest:
    path = folder / MANIFEST_NAME

    if not path.exists():
        raise McnetError(f"no {MANIFEST_NAME} in {folder}")

    raw = yaml.safe_load(path.read_text(encoding="utf-8"))

    if not isinstance(raw, dict):
        raise McnetError(f"{path} is not a mcnet manifest")

    return schema.manifest_from_dict(raw, path)


def load_server(folder: Path) -> ServerManifest:
    """Load a manifest that must be a server."""
    manifest = load_manifest(folder)

    if not isinstance(manifest, ServerManifest):
        raise McnetError(
            f"{folder} is a proxy, not a server",
            hint="use 'mcnet proxy' for proxies",
        )

    return manifest


def load_proxy(folder: Path) -> ProxyManifest:
    """Load a manifest that must be a proxy."""
    manifest = load_manifest(folder)

    if not isinstance(manifest, ProxyManifest):
        raise McnetError(
            f"{folder} is a server, not a proxy",
            hint="use 'mcnet server' for servers",
        )

    return manifest


def remove_manifest(folder: Path) -> Path:
    path = folder / MANIFEST_NAME
    path.unlink()

    return path
