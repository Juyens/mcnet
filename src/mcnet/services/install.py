from pathlib import Path

from mcnet.core.download import download, file_matches
from mcnet.core.models import LockEntry, Plugin, Server
from mcnet.services import registry


def install_fresh(
    root: Path,
    server_name: str,
    server: Server,
    plugin: Plugin,
    mc_version: str,
    lock: dict,
) -> str | None:
    api = registry.get_client(plugin.source)
    resolved = api.resolve(plugin.slug, server.loader, mc_version)

    if resolved is None:
        return None

    dest = root / server_name / "plugins" / resolved.filename

    if not file_matches(dest, resolved.hash, resolved.algorithm):
        download(
            resolved.url, resolved.hash, resolved.algorithm, resolved.filename, dest
        )

    if server_name not in lock:
        lock[server_name] = {}

    lock[server_name][plugin.slug] = LockEntry(
        source=plugin.source,
        version=resolved.version,
        filename=resolved.filename,
        hash=resolved.hash,
        algorithm=resolved.algorithm,
        url=resolved.url,
    )

    return resolved.filename


def install_from_lock(root, server_name, entry: LockEntry) -> str | None:
    dest = root / server_name / "plugins" / entry.filename

    if file_matches(dest, entry.hash, entry.algorithm):
        return entry.filename

    download(entry.url, entry.hash, entry.algorithm, entry.filename, dest)
    return entry.filename
