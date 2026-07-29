from typing import Any, Protocol

from mcnet.core.models import Resolved
from mcnet.core.types import QueryParams


class JsonClient(Protocol):
    """Anything able to fetch and decode JSON. Http is the real one."""

    def get_json(
        self,
        url: str,
        params: QueryParams | None = None,
        ttl: int = 0,
    ) -> Any: ...


class PluginProvider(Protocol):
    def resolve(self, slug: str, loader: str, mc_version: str) -> Resolved | None:
        """Return the matching jar, or None if no compatible version exists."""
        ...
