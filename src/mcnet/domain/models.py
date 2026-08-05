from dataclasses import dataclass, field
from pathlib import Path

from mcnet.domain.java import JavaSettings


@dataclass(frozen=True)
class Resolved:
    filename: str
    url: str
    hash: str
    algorithm: str
    version: str
    size: int | None = None


@dataclass
class Plugin:
    source: str
    slug: str


@dataclass(kw_only=True)
class BaseManifest:
    """A server or proxy. Its name is the folder it lives in."""


@dataclass(kw_only=True)
class ServerManifest(BaseManifest):
    loader: str
    mc_version: str
    port: int
    java: JavaSettings | None = None
    plugins: list[Plugin] = field(default_factory=list)


@dataclass(kw_only=True)
class ProxyManifest(ServerManifest):
    servers: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class Target:
    name: str
    folder: Path


@dataclass(frozen=True)
class LockedJar:
    """A jar as it was resolved: enough to fetch and verify it again."""

    source: str
    version: str
    filename: str
    hash: str
    algorithm: str
    url: str
    size: int | None = None


@dataclass
class LockFile:
    """What one server resolved to, for the loader and version it says."""

    loader: str
    mc_version: str
    server: LockedJar | None = None
    plugins: dict[str, LockedJar] = field(default_factory=dict)

    def matches(self, loader: str, mc_version: str) -> bool:
        """False when the server moved on and everything needs resolving again."""
        return self.loader == loader and self.mc_version == mc_version

    def filenames(self) -> set[str]:
        """Every jar this lock accounts for."""
        names = {jar.filename for jar in self.plugins.values()}

        if self.server is not None:
            names.add(self.server.filename)

        return names


type AnyManifest = ServerManifest | ProxyManifest
