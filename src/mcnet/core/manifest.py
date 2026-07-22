from pathlib import Path

import yaml

from mcnet import errors
from mcnet.core.models import Manifest, Plugin, Server


def load_manifest(path: Path | None = None) -> Manifest:
    if path is None:
        path = find_manifest()

    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    servers = {}

    for name, cfg in (raw.get("servers") or {}).items():
        plugins = []

        for plugin in cfg.get("plugins", []):
            plugins.append(
                Plugin(
                    source=plugin["source"],
                    slug=plugin["slug"],
                )
            )

        servers[name] = Server(
            loader=cfg["loader"],
            port=cfg["port"],
            plugins=plugins,
        )

    if "mc_version" not in raw:
        raise errors.McnetError("mcnet.yaml is missing 'mc_version'")

    return Manifest(
        project_name=raw.get("project_name", ""),
        mc_version=raw["mc_version"],
        servers=servers,
    )


def save_manifest(manifest: Manifest, path=Path("mcnet.yaml")):
    servers = {}

    for name, server in manifest.servers.items():
        plugins = []

        for plugin in server.plugins:
            plugins.append(
                {
                    "source": plugin.source,
                    "slug": plugin.slug,
                }
            )

        servers[name] = {
            "loader": server.loader,
            "port": server.port,
            "plugins": plugins,
        }

    raw = {
        "project_name": manifest.project_name,
        "mc_version": manifest.mc_version,
        "servers": servers,
    }

    path.write_text(
        yaml.safe_dump(raw, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )


def find_manifest(start: Path | None = None) -> Path:
    current = (start or Path.cwd()).resolve()

    for folder in [current, *current.parents]:
        candidate = folder / "mcnet.yaml"
        if candidate.exists():
            return candidate

    raise errors.McnetError("mcnet.yaml not found (run 'mcnet init')")
