from pathlib import Path

from mcnet.core.download import download
from mcnet.core.file import file_matches
from mcnet.core.models import LockEntry, Plugin, Server
from mcnet.services import registry


def install_fresh(
    root: Path,
    server_name: str,
    server: Server,
    plugin: Plugin,
    mc_version: str,
    lock: dict,
) -> tuple[str | None, bool]:
    api = registry.get_client(plugin.source)
    resolved = api.resolve(plugin.slug, server.loader, mc_version)

    if resolved is None:
        return None, False

    dest = root / server_name / "plugins" / resolved.filename

    did_download = False
    if not file_matches(dest, resolved.hash, resolved.algorithm):
        download(
            resolved.url, resolved.hash, resolved.algorithm, resolved.filename, dest
        )
        did_download = True

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

    return resolved.filename, did_download
