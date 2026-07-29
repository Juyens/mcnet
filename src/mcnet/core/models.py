from dataclasses import dataclass


@dataclass(frozen=True)
class Resolved:
    filename: str
    url: str
    hash: str
    algorithm: str
    version: str
