from dataclasses import dataclass, field


@dataclass
class AddServerResult:
    server_name: str
    port: int


@dataclass
class AddPluginResult:
    slug: str
    compatible: list = field(default_factory=list)
    skipped: dict = field(default_factory=dict)


@dataclass
class SyncResult:
    downloaded: list = field(default_factory=list)
    skipped: dict = field(default_factory=dict)
