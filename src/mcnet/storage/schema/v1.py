from pathlib import Path
from typing import Any

from mcnet.domain.loaders import ProxyLoader
from mcnet.domain.models import AnyManifest, Plugin, ProxyManifest, ServerManifest
from mcnet.errors import McnetError

VERSION = 1


def to_dict(manifest: AnyManifest) -> dict[str, Any]:
    if isinstance(manifest, ProxyManifest):
        return _proxy_to_dict(manifest)

    return _server_to_dict(manifest)


def from_dict(raw: dict[str, Any], path: Path) -> AnyManifest:
    loader = _require(raw, "loader", path)

    if loader in ProxyLoader:
        return _proxy_from_dict(raw, path)

    return _server_from_dict(raw, path)


def _proxy_to_dict(manifest: ProxyManifest) -> dict[str, Any]:
    plugins = []
    for plugin in manifest.plugins:
        plugins.append({"source": plugin.source, "slug": plugin.slug})

    return {
        "schema": VERSION,
        "loader": manifest.loader,
        "port": manifest.port,
        "servers": manifest.servers,
        "plugins": plugins,
    }


def _server_to_dict(manifest: ServerManifest) -> dict[str, Any]:
    plugins = []
    for plugin in manifest.plugins:
        plugins.append({"source": plugin.source, "slug": plugin.slug})

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
        plugins=_plugins(raw, path),
        servers=_servers(raw, path),
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
