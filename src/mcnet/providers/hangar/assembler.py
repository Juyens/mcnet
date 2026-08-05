from mcnet.domain.models import Resolved
from mcnet.providers.hangar.endpoints.version import VersionsResource

ALGORITHM = "sha256"


def to_resolved(data: VersionsResource, *, platform: str) -> Resolved | None:
    """Turn the newest release into a downloadable artifact.

    Hangar answers newest first for the channel asked, so the first result is
    the one wanted.
    """
    results = data.get("result") or []

    if not results:
        return None

    version = results[0]
    download = version["downloads"].get(platform)

    if download is None:
        return None

    file_info = download.get("fileInfo")
    url = download.get("downloadUrl")

    # Some plugins are hosted off Hangar, on GitHub or Patreon: they carry an
    # externalUrl and no file at all. Nothing to fetch and nothing to verify,
    # so they count as unavailable rather than as a broken download later.
    if file_info is None or url is None:
        return None

    return Resolved(
        filename=file_info["name"],
        url=url,
        hash=file_info["sha256Hash"],
        algorithm=ALGORITHM,
        version=version["name"],
        size=file_info.get("sizeBytes"),
    )
