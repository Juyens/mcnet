from mcnet.domain.models import Resolved
from mcnet.errors import NotFoundError
from mcnet.providers.papermc import assembler
from mcnet.providers.papermc.endpoints.build import BuildResource, ProjectResource
from mcnet.providers.protocols import JsonClient, ServerSource

BASE_URL = "https://fill.papermc.io/v3"
ONE_HOUR = 3600
ONE_DAY = 86400

PROJECT_ENDPOINT = "/projects/{project}"
BUILDS_ENDPOINT = "/projects/{project}/versions/{version}/builds"

# Loaders that number themselves instead of tracking Minecraft releases.
SELF_VERSIONED = frozenset({"velocity"})

# How many of its own releases to look at before settling for the newest.
CANDIDATES = 3


class PaperMcAPI(ServerSource):
    """paper, folia and velocity all live behind the same API."""

    def __init__(self, http: JsonClient) -> None:
        self._http = http

    def resolve(self, *, loader: str, mc_version: str) -> Resolved | None:
        if loader in SELF_VERSIONED:
            return self._resolve_own_release(loader)

        return self._resolve_build(loader, mc_version)

    def _resolve_build(self, project: str, version: str) -> Resolved | None:
        builds = self._builds(project, version)

        return assembler.to_resolved(builds, version=version)

    def _resolve_own_release(self, project: str) -> Resolved | None:
        """Prefer the newest line its authors mark RECOMMENDED.

        Velocity 4 ships as STABLE while 3.x stays RECOMMENDED, and plugins
        built for 3.x do not load on 4. Following the channel keeps a fresh
        proxy compatible with what Modrinth actually serves.
        """
        newest = None

        for version in self._releases(project)[:CANDIDATES]:
            builds = self._builds(project, version)
            build = assembler.best_build(builds)

            if build is None:
                continue

            if assembler.is_recommended(build):
                return assembler.to_resolved(builds, version=version)

            if newest is None:
                newest = (builds, version)

        if newest is None:
            return None

        builds, version = newest

        return assembler.to_resolved(builds, version=version)

    def _builds(self, project: str, version: str) -> list[BuildResource]:
        url = BASE_URL + BUILDS_ENDPOINT.format(project=project, version=version)

        try:
            return self._http.get_json(url, ttl=ONE_HOUR)
        except NotFoundError:
            return []

    def _releases(self, project: str) -> list[str]:
        url = BASE_URL + PROJECT_ENDPOINT.format(project=project)

        try:
            data: ProjectResource = self._http.get_json(url, ttl=ONE_DAY)
        except NotFoundError:
            return []

        return assembler.to_stable_versions(data)
