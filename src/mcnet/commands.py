import yaml

from pathlib import Path

from mcnet import errors, results
from mcnet.core import parser
from mcnet.core.manifest import load_manifest, save_manifest
from mcnet.core.models import Server
from mcnet.sources import registry
from mcnet.sources.download import download


def mcnet_init(project_name: str, mc_version: str):
    path = Path("mcnet.yaml")

    if path.exists():
        raise errors.McnetError(
            "mcnet.yaml already exists (delete it first to reinitialize)"
        )

    if project_name is None:
        project_name = Path.cwd().name

    data = {
        "project_name": project_name,
        "mc_version": mc_version,
        "servers": {},
    }

    path.write_text(
        yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8"
    )


def mcnet_add_server(server_name: str, loader: str, port: int):

    manifest = load_manifest()

    if server_name in manifest.servers:
        raise errors.McnetError(f"server '{server_name}' already exists")

    if port is None:
        used_ports = []

        for server in manifest.servers.values():
            used_ports.append(server.port)

        if loader == "velocity":
            port = 25565
        else:
            port = max(used_ports or [25565]) + 1

    manifest.servers[server_name] = Server(
        loader=loader,
        port=port,
        plugins=[],
    )

    save_manifest(manifest)

    return results.AddServerResult(server_name, port)


def mcnet_edit_server(server_name: str, new_name: str, loader: str, port: int):
    manifest = load_manifest()

    if server_name not in manifest.servers:
        raise errors.McnetError(
            f"server '{server_name}' not found (available: {', '.join(manifest.servers) or 'none'})"
        )

    server = manifest.servers[server_name]
    changes = []

    if new_name is not None:
        if new_name in manifest.servers:
            raise errors.McnetError(f"server '{new_name}' already exists")

        manifest.servers[new_name] = manifest.servers.pop(server_name)
        changes.append(f"server_name: {server_name} → {new_name}")

    if loader is not None:
        changes.append(f"loader: {server.loader} → {loader}")
        server.loader = loader

    if port is not None and port != server.port:
        for other, cfg in manifest.servers.items():
            if other != server_name and cfg.port == port:
                raise errors.McnetError(f"port {port} already used by '{other}'")
        changes.append(f"port: {server.port} → {port}")
        server.port = port

    if changes:
        save_manifest(manifest)

    return changes


def mcnet_list():
    manifest = load_manifest()
    return manifest.servers


def add_plugin(url: str, server_names: str):
    manifest = load_manifest()

    unknown = []
    names = parser.parse_list(server_names)

    for name in names:
        if name not in manifest.servers:
            unknown.append(name)

    if unknown:
        raise errors.McnetError(f"unknown servers: {', '.join(unknown)}")

    source, slug = parser.parse_plugin_url(url)

    skipped = {}
    resolved_map = {}

    mc_version = manifest.mc_version

    for name in names:
        server = manifest.servers[name]

        already = False
        for plugin in server.plugins:
            if plugin["slug"] == slug:
                already = True
                skipped[name] = f"already added from {plugin['source']}"
                break

        if already:
            continue

        loader = manifest.servers[name].loader

        api = registry.get_client(source)
        resolved = api.resolve(slug, loader, mc_version)

        if resolved is None:
            skipped[name] = f"no {loader} version for MC {mc_version}"
        else:
            resolved_map[name] = resolved

    for name, resolved in resolved_map.items():
        download(resolved, Path(name) / "plugins" / resolved.filename)
        manifest.servers[name].plugins.append({"source": source, "slug": slug})

    save_manifest(manifest)

    return results.AddPluginResult(slug, resolved_map, skipped)
