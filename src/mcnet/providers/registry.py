from mcnet.errors import McnetError
from mcnet.providers.modrinth import ModrinthAPI
from mcnet.providers.protocols import JsonClient, PluginProvider


class Providers:
    """Every provider mcnet can talk to, sharing one client."""

    def __init__(self, http: JsonClient) -> None:
        self.modrinth = ModrinthAPI(http)

        self._by_source: dict[str, PluginProvider] = {
            "modrinth": self.modrinth,
        }

    def for_source(self, source: str) -> PluginProvider:
        provider = self._by_source.get(source)

        if provider is None:
            raise McnetError(
                f"unknown source: {source}",
                hint=f"mcnet reads plugins from {', '.join(self._by_source)}",
            )

        return provider
