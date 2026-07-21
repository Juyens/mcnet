import yaml

from pathlib import Path
from mcnet import errors
from mcnet.core.models import Server, Manifest


def load_manifest(path: Path = Path("mcnet.yaml")) -> Manifest:
    if not path.exists():
        raise errors.McnetError("mcnet.yaml not found (did you run 'mcnet init'?)")

    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    servers = {}

    for name, cfg in (raw.get("servers") or {}).items():
        servers[name] = Server(
            loader=cfg["loader"],
            port=cfg["port"],
            plugins=cfg.get("plugins", []),
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
        servers[name] = {
            "loader": server.loader,
            "port": server.port,
            "plugins": server.plugins,
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
