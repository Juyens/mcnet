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


@dataclass
class Manifest:
    """A server or proxy. Its name is the folder it lives in."""

    loader: str
    mc_version: str
    port: int
    plugins: list[Plugin] = field(default_factory=list)
