from mcnet.domain.models import Resolved
from mcnet.providers.papermc.endpoints.build import BuildResource, ProjectResource

SERVER_DOWNLOAD = "server:default"

ALGORITHM = "sha256"

# How much a channel is worth trusting. Folia only ever ships ALPHA, so this
# has to be a preference with a fallback rather than a filter.
_CHANNEL_RANK = {"RECOMMENDED": 0, "STABLE": 1, "BETA": 2}
_UNRANKED = 3


def to_resolved(builds: list[BuildResource], *, version: str) -> Resolved | None:
    """Turn the steadiest recent build into a downloadable artifact."""
    build = best_build(builds)
    if build is None:
        return None

    download = build["downloads"].get(SERVER_DOWNLOAD)
    if download is None:
        return None

    return Resolved(
        filename=download["name"],
        url=download["url"],
        hash=download["checksums"][ALGORITHM],
        algorithm=ALGORITHM,
        version=f"{version}-{build['id']}",
        size=download["size"],
    )


def best_build(builds: list[BuildResource]) -> BuildResource | None:
    """The newest build of the steadiest channel that has any at all."""
    if not builds:
        return None

    steadiest = min(rank(build) for build in builds)

    return max(
        (build for build in builds if rank(build) == steadiest),
        key=lambda build: build["id"],
    )


def rank(build: BuildResource) -> int:
    return _CHANNEL_RANK.get(build["channel"], _UNRANKED)


def is_recommended(build: BuildResource) -> bool:
    return build["channel"] == "RECOMMENDED"


def to_stable_versions(project: ProjectResource) -> list[str]:
    """Released versions of a self-versioned project, newest first.

    Velocity numbers itself, so the Minecraft version says nothing about
    which one to run: snapshots are dropped and the rest sorted properly,
    since '3.10.0' has to beat '3.9.0' and a plain string sort would not.
    """
    released = []

    for family in project["versions"].values():
        for version in family:
            parts = _parts(version)

            if parts is not None:
                released.append((parts, version))

    released.sort(reverse=True)

    return [version for _, version in released]


def _parts(version: str) -> tuple[int, ...] | None:
    """The numeric parts of a release, or None for snapshots and previews."""
    parts = []

    for chunk in version.split("."):
        if not chunk.isdigit():
            return None

        parts.append(int(chunk))

    return tuple(parts)
