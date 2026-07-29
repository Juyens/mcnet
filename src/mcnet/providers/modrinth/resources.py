from typing import TypedDict


class GameVersionResource(TypedDict):
    version: str
    version_type: str
    date: str
    major: bool


class FileResource(TypedDict):
    filename: str
    url: str
    primary: bool
    hashes: dict[str, str]


class VersionResource(TypedDict):
    version_number: str
    files: list[FileResource]
