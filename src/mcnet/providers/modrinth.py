import json

import httpx

from mcnet.core import errors
from mcnet.providers.base import BaseApi, Resolved
from mcnet.providers.platform import MODRINTH


class ModrinthAPI(BaseApi):
    BASE_URL = "https://api.modrinth.com/v2"
    VERSION_ENDPOINT = "/project/{slug}/version"

    def __init__(self):
        self.client = httpx.Client(
            headers={"User-Agent": self.USER_AGENT},
            follow_redirects=True,
        )

    def _get_versions(self, slug: str, loaders: list, game_versions: list):
        """Internal: raw JSON from Modrinth."""
        url = self.BASE_URL + self.VERSION_ENDPOINT.format(slug=slug)

        params = {
            "loaders": json.dumps(loaders),
            "game_versions": json.dumps(game_versions),
        }

        response = self.client.get(url, params=params)

        if response.status_code == 404:
            raise errors.McnetError(f"'{slug}' not found on Modrinth")

        response.raise_for_status()
        return response.json()

    def resolve(self, slug: str, loader: str, mc_version: str):
        loaders = MODRINTH[loader]
        versions = self._get_versions(slug, loaders, game_versions=[mc_version])

        if not versions:
            return None

        version = versions[0]

        primary = {}
        for file in version["files"]:
            if file["primary"]:
                primary = file
                break

        return Resolved(
            filename=primary["filename"],
            url=primary["url"],
            hash=primary["hashes"]["sha512"],
            algorithm="sha512",
            version=version["version_number"],
        )
