from pathlib import Path
from typing import Any

from mcnet.domain import loaders
from mcnet.domain.models import (
    AnyManifest,
    LockedJar,
    LockFile,
    Plugin,
    ProxyManifest,
    ServerManifest,
)
from mcnet.errors import McnetError

VERSION = 1


def manifest_to_dict(manifest: AnyManifest) -> dict[str, Any]:
    if isinstance(manifest, ProxyManifest):
        return _proxy_to_dict(manifest)

    return _server_to_dict(manifest)


def manifest_from_dict(raw: dict[str, Any], path: Path) -> AnyManifest:
    loader = _require_str(raw, "loader", path)

    # The loader picks which API the jar comes from, so an unknown one has to
    # fail here rather than halfway through a sync.
    if loader not in loaders.KNOWN:
        raise McnetError(
            f"{path}: '{loader}' is not server software mcnet knows",
            hint=f"use one of {loaders.LISTING}",
        )

    if loaders.is_proxy(loader):
        return _proxy_from_dict(raw, path)

    return _server_from_dict(raw, path)


def lock_to_dict(lock: LockFile) -> dict[str, Any]:
    raw: dict[str, Any] = {
        "schema": VERSION,
        "loader": lock.loader,
        "mc_version": lock.mc_version,
        "plugins": {slug: _jar_to_dict(jar) for slug, jar in lock.plugins.items()},
    }

    if lock.server is not None:
        raw["server"] = _jar_to_dict(lock.server)

    return raw


def lock_from_dict(raw: dict[str, Any], path: Path) -> LockFile:
    return LockFile(
        loader=_require_str(raw, "loader", path),
        mc_version=_require_str(raw, "mc_version", path),
        server=_locked_server(raw, path),
        plugins=_locked_plugins(raw, path),
    )


def _jar_to_dict(jar: LockedJar) -> dict[str, Any]:
    raw: dict[str, Any] = {
        "source": jar.source,
        "version": jar.version,
        "filename": jar.filename,
        "hash": jar.hash,
        "algorithm": jar.algorithm,
        "url": jar.url,
    }

    # Purpur publishes no size, so the key is absent rather than a fake zero.
    if jar.size is not None:
        raw["size"] = jar.size

    return raw


def _jar_from_dict(raw: dict[str, Any], path: Path) -> LockedJar:
    return LockedJar(
        source=_require_str(raw, "source", path),
        version=_require_str(raw, "version", path),
        filename=_require_str(raw, "filename", path),
        hash=_require_str(raw, "hash", path),
        algorithm=_require_str(raw, "algorithm", path),
        url=_require_str(raw, "url", path),
        size=_optional_int(raw, "size", path),
    )


def _locked_server(raw: dict[str, Any], path: Path) -> LockedJar | None:
    entry = raw.get("server")

    if entry is None:
        return None

    if not isinstance(entry, dict):
        raise McnetError(f"{path} has a malformed server entry")

    return _jar_from_dict(entry, path)


def _locked_plugins(raw: dict[str, Any], path: Path) -> dict[str, LockedJar]:
    entries = raw.get("plugins") or {}

    if not isinstance(entries, dict):
        raise McnetError(f"{path} has a malformed plugins section")

    plugins = {}

    for slug, entry in entries.items():
        if not isinstance(entry, dict):
            raise McnetError(f"{path} has a malformed entry for '{slug}'")

        plugins[slug] = _jar_from_dict(entry, path)

    return plugins


def _proxy_to_dict(manifest: ProxyManifest) -> dict[str, Any]:
    plugins = []
    for plugin in manifest.plugins:
        plugins.append({"slug": plugin.slug, "source": plugin.source})

    return {
        "schema": VERSION,
        "loader": manifest.loader,
        "mc_version": manifest.mc_version,
        "port": manifest.port,
        "servers": manifest.servers,
        "plugins": plugins,
    }


def _server_to_dict(manifest: ServerManifest) -> dict[str, Any]:
    plugins = []
    for plugin in manifest.plugins:
        plugins.append({"slug": plugin.slug, "source": plugin.source})

    return {
        "schema": VERSION,
        "loader": manifest.loader,
        "mc_version": manifest.mc_version,
        "port": manifest.port,
        "plugins": plugins,
    }


def _require(raw: dict[str, Any], key: str, path: Path) -> Any:
    if key not in raw:
        raise McnetError(f"{path} is missing '{key}'")

    return raw[key]


def _require_str(raw: dict[str, Any], key: str, path: Path) -> str:
    value = _require(raw, key, path)

    if not isinstance(value, str):
        raise McnetError(
            f"{path}: '{key}' must be text",
            hint=f'write it as "{value}" between quotes',
        )

    return value


def _optional_int(raw: dict[str, Any], key: str, path: Path) -> int | None:
    if raw.get(key) is None:
        return None

    return _require_int(raw, key, path)


def _require_int(raw: dict[str, Any], key: str, path: Path) -> int:
    value = _require(raw, key, path)

    if isinstance(value, bool) or not isinstance(value, int):
        raise McnetError(f"{path}: '{key}' must be a whole number")

    return value


def _server_from_dict(raw: dict[str, Any], path: Path) -> ServerManifest:
    return ServerManifest(
        loader=_require_str(raw, "loader", path),
        port=_require_int(raw, "port", path),
        plugins=_plugins(raw, path),
        mc_version=_require_str(raw, "mc_version", path),
    )


def _proxy_from_dict(raw: dict[str, Any], path: Path) -> ProxyManifest:
    return ProxyManifest(
        loader=_require_str(raw, "loader", path),
        port=_require_int(raw, "port", path),
        mc_version=_require_str(raw, "mc_version", path),
        servers=_servers(raw, path),
        plugins=_plugins(raw, path),
    )


def _servers(raw: dict[str, Any], path: Path) -> list[str]:
    servers = []

    for entry in raw.get("servers") or []:
        if not isinstance(entry, dict):
            raise McnetError(f"{path} has a malformed servers entry")

        servers.append(entry)

    return servers


def _plugins(raw: dict[str, Any], path: Path) -> list[Plugin]:
    plugins = []

    for entry in raw.get("plugins") or []:
        if not isinstance(entry, dict):
            raise McnetError(f"{path} has a malformed plugin entry")

        plugins.append(
            Plugin(
                source=_require(entry, "source", path),
                slug=_require(entry, "slug", path),
            )
        )

    return plugins
