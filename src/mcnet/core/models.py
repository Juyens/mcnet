from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Resolved:
    filename: str
    url: str
    hash: str
    algorithm: str
    version: str


@dataclass
class LockEntry:
    source: str
    version: str
    filename: str
    hash: str
    algorithm: str
    url: str


@dataclass
class DownloadTask:
    key: str
    url: str
    hash: str
    algorithm: str
    filename: str
    dest: Path


@dataclass
class Plugin:
    source: str
    slug: str


@dataclass
class Server:
    loader: str
    port: int
    plugins: list[Plugin] = field(default_factory=list)


@dataclass
class Manifest:
    project_name: str
    mc_version: str
    servers: dict[str, Server] = field(default_factory=dict)
