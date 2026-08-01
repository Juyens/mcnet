from dataclasses import dataclass, field


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

    loader: str
    port: int
    plugins: list[Plugin] = field(default_factory=list)


@dataclass(kw_only=True)
class ServerManifest(BaseManifest):
    mc_version: str


@dataclass(kw_only=True)
class ProxyManifest(BaseManifest):
    servers: list[str] = field(default_factory=list)


type AnyManifest = ServerManifest | ProxyManifest
