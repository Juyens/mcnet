from mcnet.core.models import Resolved
from mcnet.providers.modrinth.resources import GameVersionResource, VersionResource


class ModrinthAssembler:
    @staticmethod
    def to_release_versions(resources: list[GameVersionResource]) -> list[str]:
        versions = []
        for resource in resources:
            if resource["version_type"] == "release":
                versions.append(resource["version"])

        return versions

    @staticmethod
    def to_resolved(resource: VersionResource) -> Resolved | None:
        primary = None
        for file in resource["files"]:
            if file["primary"]:
                primary = file
                break

        if primary is None:
            return None

        return Resolved(
            filename=primary["filename"],
            url=primary["url"],
            hash=primary["hashes"]["sha512"],
            algorithm="sha512",
            version=resource["version_number"],
        )
