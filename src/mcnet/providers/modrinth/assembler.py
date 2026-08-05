from mcnet.domain.models import Resolved
from mcnet.providers.modrinth.endpoints.game_versions import GameVersionResource
from mcnet.providers.modrinth.endpoints.version import FileResource, VersionResource


def to_release_versions(resources: list[GameVersionResource]) -> list[str]:
    versions = []
    for resource in resources:
        if resource["version_type"] == "release":
            versions.append(resource["version"])

    return versions


def to_resolved(resources: list[VersionResource]) -> Resolved | None:
    """Turn the newest compatible version into a downloadable artifact."""
    version = _newest(resources)
    if version is None:
        return None

    primary = _primary_file(version)
    if primary is None:
        return None

    return Resolved(
        filename=primary["filename"],
        url=primary["url"],
        hash=primary["hashes"]["sha512"],
        algorithm="sha512",
        version=version["version_number"],
        size=primary["size"],
    )


def _newest(resources: list[VersionResource]) -> VersionResource | None:
    chosen = None

    for resource in resources:
        if chosen is None or resource["date_published"] > chosen["date_published"]:
            chosen = resource

    return chosen


def _primary_file(version: VersionResource) -> FileResource | None:
    for file in version["files"]:
        if file["primary"]:
            return file

    return None
