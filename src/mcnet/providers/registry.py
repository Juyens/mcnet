from mcnet.core.error import McnetError
from mcnet.core.paths import cache_dir
from mcnet.providers.base import PluginProvider
from mcnet.providers.http import Http
from mcnet.providers.modrinth import ModrinthAPI

USER_AGENT = "juyens/mcnet (joseph.juliuscb@gmail.com)"


class Providers:
    def __init__(self, http: Http) -> None:
        self.modrinth = ModrinthAPI(http)

    def for_source(self, source: str) -> PluginProvider:
        available: dict[str, PluginProvider] = {
            "modrinth": self.modrinth,
        }

        if source not in available:
            raise McnetError(f"unknown source: {source}")

        return available[source]


_providers: Providers | None = None


def get_providers() -> Providers:
    global _providers
    if _providers is None:
        _providers = Providers(Http(USER_AGENT, cache_dir()))
    return _providers
