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
class Incompatible:
    name: str
    loader: str
    mc_version: str


@dataclass
class AddResult:
    slug: str
    added: list[str] = field(default_factory=list)
    already: list[str] = field(default_factory=list)
    incompatible: list[Incompatible] = field(default_factory=list)
    unknown: list[str] = field(default_factory=list)
    verified: bool = True


type AnyManifest = ServerManifest | ProxyManifest
