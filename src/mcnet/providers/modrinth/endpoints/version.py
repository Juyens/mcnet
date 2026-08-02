from typing import TypedDict


class HashesResource(TypedDict):
    sha1: str
    sha512: str


class FileResource(TypedDict):
    id: str
    hashes: HashesResource
    url: str
    filename: str
    primary: bool
    size: int
    file_type: str | None


class VersionResource(TypedDict):
    id: str
    project_id: str
    author_id: str
    name: str
    version_number: str
    version_type: str
    status: str
    requested_status: str | None
    changelog: str
    changelog_url: str | None
    date_published: str
    downloads: int
    featured: bool
    game_versions: list[str]
    loaders: list[str]
    files: list[FileResource]
