from typing import TypedDict


class ChecksumResource(TypedDict):
    sha256: str


class DownloadResource(TypedDict):
    name: str
    checksums: ChecksumResource
    size: int
    url: str


class BuildResource(TypedDict):
    id: int
    time: str
    channel: str
    downloads: dict[str, DownloadResource]


class ProjectResource(TypedDict):
    project: dict[str, str]
    versions: dict[str, list[str]]
