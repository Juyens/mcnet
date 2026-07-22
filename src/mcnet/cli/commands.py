from pathlib import Path

import httpx
import yaml

from mcnet.core import errors, results
from mcnet.core.models import Plugin, Server
from mcnet.services import parser
from mcnet.services.install import install_fresh, install_from_lock
from mcnet.services.lock import load_lock, save_lock
from mcnet.services.manifest import find_manifest, load_manifest, save_manifest


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
        changes.append(f"server_name: {server_name} -> {new_name}")

    if loader is not None:
        changes.append(f"loader: {server.loader} -> {loader}")
        server.loader = loader

    if port is not None and port != server.port:
        for other, cfg in manifest.servers.items():
            if other != server_name and cfg.port == port:
                raise errors.McnetError(f"port {port} already used by '{other}'")
        changes.append(f"port: {server.port} -> {port}")
        server.port = port

    if changes:
        save_manifest(manifest)

    return changes


def mcnet_list():
    manifest = load_manifest()
    return manifest.servers


def mcnet_add_plugin(url: str, server_names: str):
    manifest = load_manifest()

    root = find_manifest().parent
    lock = load_lock(root)

    unknown = []
    names = parser.parse_list(server_names)

    for name in names:
        if name not in manifest.servers:
            unknown.append(name)

    if unknown:
        raise errors.McnetError(f"unknown servers: {', '.join(unknown)}")

    source, slug = parser.parse_plugin_url(url)

    skipped = {}
    compatible = []

    for name in names:
        server = manifest.servers[name]

        already = False
        for plugin in server.plugins:
            if plugin.slug == slug:
                already = True
                skipped[name] = f"already added from {plugin.source}"
                break

        if already:
            continue

        loader = manifest.servers[name].loader

        filename, _ = install_fresh(
            root, name, server, Plugin(source, slug), manifest.mc_version, lock
        )

        if filename is None:
            skipped[name] = f"no {loader} version for MC {manifest.mc_version}"
        else:
            manifest.servers[name].plugins.append(Plugin(source, slug))
            compatible.append(name)

    save_manifest(manifest)
    save_lock(root, lock)

    return results.AddPluginResult(slug, compatible, skipped)


def mcnet_sync():
    manifest = load_manifest()

    root = find_manifest().parent
    lock = load_lock(root)

    downloaded = []
    up_to_date = []
    skipped = {}

    for name, server in manifest.servers.items():
        for plugin in server.plugins:
            try:
                locked = lock.get(name, {}).get(plugin.slug)
                if locked is not None:
                    filename, did_download = install_from_lock(root, name, locked)
                else:
                    filename, did_download = install_fresh(
                        root, name, server, plugin, manifest.mc_version, lock
                    )

                if filename is None:
                    skipped[f"{name}/{plugin.slug}"] = f"no {server.loader} version"
                elif did_download:
                    downloaded.append(f"{name}/{filename}")
                else:
                    up_to_date.append(f"{name}/{filename}")

            except (errors.McnetError, httpx.HTTPError) as e:
                skipped[f"{name}/{plugin.slug}"] = f"download failed: {e}"

    save_lock(root, lock)

    return results.SyncResult(downloaded, up_to_date, skipped)


def mcnet_remove_server(server_name: str):
    root = find_manifest().parent
    manifest = load_manifest()

    if server_name not in manifest.servers:
        raise errors.McnetError(f"server '{server_name}' not found")

    del manifest.servers[server_name]
    save_manifest(manifest)

    lock = load_lock(root)
    lock.pop(server_name, None)
    save_lock(root, lock)


def mcnet_remove_plugin(slug: str, server_names: str):
    root = find_manifest().parent
    manifest = load_manifest()
    lock = load_lock(root)

    names = parser.parse_list(server_names)

    unknown = []

    for name in names:
        if name not in manifest.servers:
            unknown.append(name)

    if unknown:
        raise errors.McnetError(f"unknown servers: {', '.join(unknown)}")

    removed = []
    skipped = []

    for name in names:
        server = manifest.servers[name]

        before = len(server.plugins)

        kept = []
        for plugin in server.plugins:
            if plugin.slug != slug:
                kept.append(plugin)

        server.plugins = kept

        if len(server.plugins) < before:
            lock.get(name, {}).pop(slug, None)
            removed.append(name)
        else:
            skipped.append(name)

        if name in lock and not lock[name]:
            del lock[name]

    if not removed:
        raise errors.McnetError(f"'{slug}' not found on any of those servers")

    save_manifest(manifest)
    save_lock(root, lock)

    return results.RemovePluginResult(removed, skipped)


def mcnet_update(slug: str | None = None):
    path = find_manifest()
    root = path.parent
    manifest = load_manifest(path)
    lock = load_lock(root)

    updated = []
    unchanged = []
    skipped = {}
    touched = False

    for name, server in manifest.servers.items():
        for plugin in server.plugins:
            if slug is not None and plugin.slug != slug:
                continue

            touched = True
            key = f"{name}/{plugin.slug}"

            old = lock.get(name, {}).get(plugin.slug)

            if old:
                old_version = old.version
            else:
                old_version = None

            try:
                filename, _ = install_fresh(
                    root, name, server, plugin, manifest.mc_version, lock
                )
            except (errors.McnetError, httpx.HTTPError) as e:
                skipped[key] = f"update failed: {e}"
                continue

            if filename is None:
                skipped[key] = f"no {server.loader} version"
                continue

            new_version = lock[name][plugin.slug].version

            if old_version != new_version:
                updated.append(f"{key}: {old_version} -> {new_version}")
            else:
                unchanged.append(key)

    if slug is not None and not touched:
        raise errors.McnetError(f"'{slug}' not found in the manifest")

    save_lock(root, lock)

    return results.UpdateResult(updated, unchanged, skipped)
