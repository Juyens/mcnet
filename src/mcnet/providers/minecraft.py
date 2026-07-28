from typing import TypedDict

from mcnet.providers.http import Http

GAME_VERSIONS_URL = "https://api.modrinth.com/v2/tag/game_version"
ONE_DAY = 86400


class GameVersion(TypedDict):
    version: str
    version_type: str
    date: str
    major: bool


class MinecraftVersions:
    def __init__(self, http: Http) -> None:
        self._http = http

    def releases(self) -> list[str]:
        data: list[GameVersion] = self._http.get_json(GAME_VERSIONS_URL, ttl=ONE_DAY)

        versions = []
        for entry in data:
            if entry["version_type"] == "release":
                versions.append(entry["version"])

        return versions
