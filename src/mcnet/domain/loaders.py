from enum import StrEnum


class ServerLoader(StrEnum):
    """Server software mcnet can fetch. Spigot and Bukkit ship no binaries."""

    PAPER = "paper"
    PURPUR = "purpur"
    FOLIA = "folia"


class ProxyLoader(StrEnum):
    """Proxy software mcnet can fetch."""

    VELOCITY = "velocity"


KNOWN: frozenset[str] = frozenset([*ServerLoader, *ProxyLoader])

LISTING = ", ".join([*ServerLoader, *ProxyLoader])


def is_proxy(loader: str) -> bool:
    """Whether a loader stands in front of servers instead of being one."""
    return loader in ProxyLoader
