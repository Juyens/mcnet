from mcnet.domain.models import Resolved
from mcnet.errors import NotFoundError
from mcnet.providers.protocols import JsonClient, ServerSource
from mcnet.providers.purpur import assembler
from mcnet.providers.purpur.endpoints.build import BuildResource

BASE_URL = "https://api.purpurmc.org/v2/purpur"
ONE_HOUR = 3600

LATEST_ENDPOINT = "/{version}/latest"
DOWNLOAD_ENDPOINT = "/{version}/{build}/download"


class PurpurAPI(ServerSource):
    def __init__(self, http: JsonClient) -> None:
        self._http = http

    def resolve(self, *, loader: str, mc_version: str) -> Resolved | None:
        url = BASE_URL + LATEST_ENDPOINT.format(version=mc_version)

        try:
            build: BuildResource = self._http.get_json(url, ttl=ONE_HOUR)
        except NotFoundError:
            return None

        return assembler.to_resolved(build, download_url=self._download(build))

    def _download(self, build: BuildResource) -> str:
        return BASE_URL + DOWNLOAD_ENDPOINT.format(
            version=build["version"], build=build["build"]
        )
