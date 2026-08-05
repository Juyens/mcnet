import json

from mcnet.domain.models import Resolved
from mcnet.providers.modrinth import assembler
from mcnet.providers.modrinth.endpoints.game_versions import GameVersionResource
from mcnet.providers.modrinth.endpoints.version import VersionResource
from mcnet.providers.protocols import JsonClient, Provider

BASE_URL = "https://api.modrinth.com/v2"
ONE_DAY = 86400

GAME_VERSION_ENDPOINT = "/tag/game_version"
VERSION_ENDPOINT = "/project/{slug}/version"


class ModrinthAPI(Provider):
    def __init__(self, http: JsonClient) -> None:
        self._http = http

    def game_versions(self) -> list[str]:
        data: list[GameVersionResource] = self._http.get_json(
            BASE_URL + GAME_VERSION_ENDPOINT, ttl=ONE_DAY
        )

        return assembler.to_release_versions(data)

    def resolve(self, slug: str, *, loader: str, mc_version: str) -> Resolved | None:
        data: list[VersionResource] = self._http.get_json(
            BASE_URL + VERSION_ENDPOINT.format(slug=slug),
            params={
                "loaders": _array(loader),
                "game_versions": _array(mc_version),
            },
            ttl=ONE_DAY,
        )

        return assembler.to_resolved(data)


def _array(*values: str) -> str:
    """Modrinth drops these filters unless they arrive as a JSON array."""
    return json.dumps(values)
