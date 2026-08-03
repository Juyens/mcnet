from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class Resolved:
    filename: str
    url: str
    hash: str
    algorithm: str
    version: str


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
    plugins: list[Plugin] = field(default_factory=list)


@dataclass(kw_only=True)
class ProxyManifest(ServerManifest):
    servers: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class Target:
    name: str
    folder: Path


@dataclass(frozen=True)
class LockedPlugin:
    source: str
    version: str
    filename: str
    hash: str
    algorithm: str
    url: str


@dataclass
class LockFile:
    loader: str
    mc_version: str
    plugins: dict[str, LockedPlugin] = field(default_factory=dict)


type AnyManifest = ServerManifest | ProxyManifest
