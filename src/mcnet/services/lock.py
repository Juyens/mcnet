import json
from dataclasses import asdict
from pathlib import Path

from mcnet.core.models import LockEntry

LOCK_NAME = "mcnet.lock.json"


def load_lock(root: Path) -> dict:
    path = root / LOCK_NAME

    if not path.exists():
        return {}

    raw = json.loads(path.read_text(encoding="utf-8"))

    lock = {}
    for server_name, plugins in raw.items():
        lock[server_name] = {}
        for slug, entry in plugins.items():
            lock[server_name][slug] = LockEntry(**entry)

    return lock


def save_lock(root: Path, lock: dict):
    path = root / LOCK_NAME

    raw = {}
    for server_name, plugins in lock.items():
        raw[server_name] = {}
        for slug, entry in plugins.items():
            raw[server_name][slug] = asdict(entry)

    path.write_text(
        json.dumps(raw, indent=2, sort_keys=True, ensure_ascii=False), encoding="utf-8"
    )
