from mcnet.domain.loaders import LISTING, ProxyLoader, ServerLoader
from mcnet.errors import McnetError
from mcnet.providers.modrinth import ModrinthAPI
from mcnet.providers.papermc import PaperMcAPI
from mcnet.providers.protocols import JsonClient, Provider, ServerSource
from mcnet.providers.purpur import PurpurAPI


class Providers:
    """Every provider mcnet can talk to, sharing one client."""

    def __init__(self, http: JsonClient) -> None:
        self.modrinth = ModrinthAPI(http)
        self.papermc = PaperMcAPI(http)
        self.purpur = PurpurAPI(http)

        self._by_source: dict[str, Provider] = {
            "modrinth": self.modrinth,
        }

        self._by_loader: dict[str, ServerSource] = {
            ServerLoader.PAPER: self.papermc,
            ServerLoader.FOLIA: self.papermc,
            ProxyLoader.VELOCITY: self.papermc,
            ServerLoader.PURPUR: self.purpur,
        }

    def for_source(self, source: str) -> Provider:
        """Where a plugin comes from."""
        provider = self._by_source.get(source)

        if provider is None:
            raise McnetError(
                f"unknown source: {source}",
                hint=f"mcnet reads plugins from {', '.join(self._by_source)}",
            )

        return provider

    def for_loader(self, loader: str) -> ServerSource:
        """Where the jar of a server or proxy comes from."""
        source = self._by_loader.get(loader)

        if source is None:
            raise McnetError(
                f"mcnet cannot download {loader}",
                hint=f"use one of {LISTING}",
            )

        return source
