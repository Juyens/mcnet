from dataclasses import dataclass, field


@dataclass
class AddServerResult:
    server_name: str
    port: int


@dataclass
class AddPluginResult:
    slug: str
    resolved_map: dict = field(default_factory=dict)
    skipped: dict = field(default_factory=dict)
