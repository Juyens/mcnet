import json
from pathlib import Path

from mcnet.domain.models import AnyManifest, LockFile
from mcnet.errors import McnetError
from mcnet.storage import schema

LOCK_NAME = "mcnet.lock.json"


def save_lock(lock: LockFile, folder: Path) -> Path:
    path = folder / LOCK_NAME
    path.write_text(
        json.dumps(schema.lock_to_dict(lock), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    return path


def load_lock(folder: Path, manifest: AnyManifest) -> LockFile:
    path = folder / LOCK_NAME

    if not path.exists():
        return LockFile(loader=manifest.loader, mc_version=manifest.mc_version)

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise McnetError(
            f"{path} is not valid JSON",
            hint="delete it and run 'mcnet sync' to rebuild it",
        ) from e

    if not isinstance(raw, dict):
        raise McnetError(f"{path} is not a mcnet lock")

    return schema.lock_from_dict(raw, path)


def remove_lock(folder: Path) -> Path | None:
    """Drop the lock if there is one."""
    path = folder / LOCK_NAME

    if not path.exists():
        return None

    path.unlink()

    return path
