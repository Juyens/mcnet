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
class RemoveResult:
    slug: str
    removed: list[str] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)
    unknown: list[str] = field(default_factory=list)
    deleted: list[str] = field(default_factory=list)
    failed: list[Failed] = field(default_factory=list)
