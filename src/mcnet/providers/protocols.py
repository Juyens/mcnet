from collections.abc import Mapping
from pathlib import Path
from typing import Any, Protocol

from mcnet.domain.models import Resolved

type QueryParams = Mapping[str, str | int | float | bool | None]


class JsonClient(Protocol):
    """Anything able to fetch and decode JSON. Http is the real one."""

    def get_json(
        self,
        url: str,
        params: QueryParams | None = None,
        ttl: int = 0,
    ) -> Any: ...


class Downloader(Protocol):
    """Anything able to fetch a file and vouch for it. Http is the real one."""

    def download(self, url: str, dest: Path, *, expected: str, algorithm: str) -> bool:
        """Fetch url into dest. False when dest already had the expected hash."""
        ...


class Provider(Protocol):
    def resolve(self, slug: str, *, loader: str, mc_version: str) -> Resolved | None:
        """Return the matching jar, or None if no compatible version exists."""
        ...


class ServerSource(Protocol):
    """Where the server or proxy jar itself comes from, one per loader family."""

    def resolve(self, *, loader: str, mc_version: str) -> Resolved | None:
        """Return the jar to run, or None if that loader has no build for it."""
        ...
