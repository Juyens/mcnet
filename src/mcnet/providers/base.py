from typing import Protocol

from mcnet.core.models import Resolved


class PluginProvider(Protocol):
    def resolve(self, slug: str, loader: str, mc_version: str) -> Resolved | None:
        """Return the matching jar, or None if no compatible version exists."""
        ...
