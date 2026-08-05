from typing import TypedDict


class BuildResource(TypedDict):
    project: str
    version: str
    build: str
    result: str
    timestamp: int
    md5: str
