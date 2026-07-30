from pathlib import Path

import yaml

from mcnet.core.models import Manifest

MANIFEST_NAME = "mcnet.yaml"
SCHEMA = 1


def save(manifest: Manifest, folder: Path) -> Path:
    plugins = []
    for plugin in manifest.plugins:
        plugins.append({"source": plugin.source, "slug": plugin.slug})

    data = {
        "schema": SCHEMA,
        "name": manifest.name,
        "loader": manifest.loader,
        "mc_version": manifest.mc_version,
        "port": manifest.port,
        "plugins": plugins,
    }

    path = folder / MANIFEST_NAME
    path.write_text(
        yaml.safe_dump(data, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )

    return path
