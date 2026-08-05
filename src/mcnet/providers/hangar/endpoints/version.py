from typing import TypedDict

# Hangar answers in camelCase. These mirror the wire exactly, so the names
# stay as they arrive rather than as Python would prefer them.


class FileInfoResource(TypedDict):
    name: str
    sizeBytes: int
    sha256Hash: str


class DownloadResource(TypedDict):
    fileInfo: FileInfoResource | None
    externalUrl: str | None
    downloadUrl: str | None


class ChannelResource(TypedDict):
    name: str


class VersionResource(TypedDict):
    name: str
    channel: ChannelResource
    downloads: dict[str, DownloadResource]


class VersionsResource(TypedDict):
    result: list[VersionResource]
