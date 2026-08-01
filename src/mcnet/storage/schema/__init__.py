from collections.abc import Callable
from pathlib import Path
from typing import Any

from mcnet.domain.models import AnyManifest
from mcnet.errors import McnetError
from mcnet.storage.schema import v1

CURRENT = v1.VERSION

_READERS: dict[int, Callable[[dict[str, Any], Path], AnyManifest]] = {
    v1.VERSION: v1.from_dict,
}


def to_dict(manifest: AnyManifest) -> dict[str, Any]:
    """Manifests are always written in the current schema."""
    return v1.to_dict(manifest)


def from_dict(raw: dict[str, Any], path: Path) -> AnyManifest:
    version = raw.get("schema")

    if not isinstance(version, int):
        raise McnetError(f"{path} is not a mcnet manifest")

    reader = _READERS.get(version)

    if reader is None:
        if version > CURRENT:
            raise McnetError(
                f"{path} needs a newer mcnet "
                f"(schema {version}, this one reads {CURRENT})"
            )

        raise McnetError(f"{path} has an unknown schema: {version}")

    return reader(raw, path)
