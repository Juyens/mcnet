from mcnet.core.models import Resolved
from mcnet.providers.base import PluginProvider
from mcnet.providers.http import Http
from mcnet.providers.modrinth.assembler import ModrinthAssembler
from mcnet.providers.modrinth.resources import GameVersionResource

BASE_URL = "https://api.modrinth.com/v2"
ONE_DAY = 86400

GAME_VERSION_ENDPOINT = "/tag/game_version"


class ModrinthAPI(PluginProvider):
    def __init__(self, http: Http) -> None:
        self._http = http
        self._assembler = ModrinthAssembler()

    def game_versions(self) -> list[str]:
        data: list[GameVersionResource] = self._http.get_json(
            BASE_URL + GAME_VERSION_ENDPOINT, ttl=ONE_DAY
        )

        return self._assembler.to_release_versions(data)

    def resolve(self, slug: str, loader: str, mc_version: str) -> Resolved | None:
        return None
