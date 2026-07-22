from concurrent.futures import ThreadPoolExecutor, as_completed

import httpx

from mcnet.core import errors
from mcnet.services import registry


def resolve_plugin(server, plugin, mc_version):
    api = registry.get_client(plugin.source)
    return api.resolve(plugin.slug, server.loader, mc_version)


def resolve_all(jobs, mc_version):
    resolved = {}

    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = {}
        for key, name, server, plugin in jobs:
            future = pool.submit(resolve_plugin, server, plugin, mc_version)
            futures[future] = key

        for future in as_completed(futures):
            key = futures[future]
            try:
                resolved[key] = future.result()
            except errors.McnetError, httpx.HTTPError:
                resolved[key] = None

    return resolved
