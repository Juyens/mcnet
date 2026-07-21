from dataclasses import dataclass, field


@dataclass
class Server:
    loader: str
    port: int
    plugins: list = field(default_factory=list)


@dataclass
class Manifest:
    project_name: str
    mc_version: str
    servers: dict[str, Server] = field(default_factory=dict)
