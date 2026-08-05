from collections.abc import Callable
from pathlib import Path
from typing import Any

from mcnet.domain.models import AnyManifest, LockFile
from mcnet.errors import McnetError
from mcnet.storage.schema import v1

CURRENT = v1.VERSION

type Reader[T] = Callable[[dict[str, Any], Path], T]

_MANIFEST_READERS: dict[int, Reader[AnyManifest]] = {
    v1.VERSION: v1.manifest_from_dict,
}

_LOCK_READERS: dict[int, Reader[LockFile]] = {
    v1.VERSION: v1.lock_from_dict,
}


def manifest_to_dict(manifest: AnyManifest) -> dict[str, Any]:
    """Manifests are always written in the current schema."""
    return v1.manifest_to_dict(manifest)


def manifest_from_dict(raw: dict[str, Any], path: Path) -> AnyManifest:
    return _read(raw, path, _MANIFEST_READERS, "manifest")


def lock_to_dict(lock: LockFile) -> dict[str, Any]:
    """Locks are always written in the current schema."""
    return v1.lock_to_dict(lock)


def lock_from_dict(raw: dict[str, Any], path: Path) -> LockFile:
    return _read(raw, path, _LOCK_READERS, "lock")


def _read[T](
    raw: dict[str, Any], path: Path, readers: dict[int, Reader[T]], noun: str
) -> T:
    version = raw.get("schema")

    if not isinstance(version, int):
        raise McnetError(f"{path} is not a mcnet {noun}")

    reader = readers.get(version)

    if reader is None:
        if version > CURRENT:
            raise McnetError(
                f"{path} needs a newer mcnet "
                f"(schema {version}, this one reads {CURRENT})"
            )

        raise McnetError(f"{path} has an unknown schema: {version}")

    return reader(raw, path)
