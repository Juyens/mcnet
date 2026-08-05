from mcnet.domain.models import Resolved
from mcnet.providers.purpur.endpoints.build import BuildResource

ALGORITHM = "md5"

SUCCESS = "SUCCESS"


def to_resolved(build: BuildResource, *, download_url: str) -> Resolved | None:
    """Turn the latest build into a downloadable artifact.

    Purpur names neither the file nor its size, so the name is rebuilt from
    the pattern its CDN serves and the size is left unknown.
    """
    if build.get("result") != SUCCESS:
        return None

    version = build["version"]
    number = build["build"]

    return Resolved(
        filename=f"purpur-{version}-{number}.jar",
        url=download_url,
        hash=build["md5"],
        algorithm=ALGORITHM,
        version=f"{version}-{number}",
        size=None,
    )
