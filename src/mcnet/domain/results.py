from dataclasses import dataclass, field


@dataclass(frozen=True)
class Incompatible:
    name: str
    loader: str
    mc_version: str


@dataclass(frozen=True)
class Failed:
    name: str
    reason: str


@dataclass
class AddResult:
    slug: str
    added: list[str] = field(default_factory=list)
    already: list[str] = field(default_factory=list)
    incompatible: list[Incompatible] = field(default_factory=list)
    unknown: list[str] = field(default_factory=list)
    downloaded: list[str] = field(default_factory=list)
    pending: list[str] = field(default_factory=list)
    failed: list[Failed] = field(default_factory=list)
    verified: bool = True


@dataclass
class ServerSync:
    """What one sync did to one server. Names here are filenames."""

    name: str
    downloaded: list[str] = field(default_factory=list)
    current: list[str] = field(default_factory=list)
    removed: list[str] = field(default_factory=list)
    failed: list[Failed] = field(default_factory=list)

    @property
    def touched(self) -> bool:
        return bool(self.downloaded or self.removed)


@dataclass
class SyncResult:
    servers: list[ServerSync] = field(default_factory=list)

    @property
    def failed(self) -> bool:
        return any(server.failed for server in self.servers)


@dataclass
class RemoveResult:
    slug: str
    removed: list[str] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)
    unknown: list[str] = field(default_factory=list)
    deleted: list[str] = field(default_factory=list)
    failed: list[Failed] = field(default_factory=list)
