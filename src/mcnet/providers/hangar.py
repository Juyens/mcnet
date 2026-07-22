import httpx

from mcnet.core import errors
from mcnet.providers.base import BaseApi, Resolved
from mcnet.providers.platform import HANGAR


class HangarAPI(BaseApi):
    BASE_URL = "https://hangar.papermc.io/api/v1"
    VERSIONS_ENDPOINT = "/projects/{slug}/versions"

    def __init__(self):
        self.client = self.client = httpx.Client(
            headers={"User-Agent": self.USER_AGENT},
            follow_redirects=True,
        )

    def _get_versions(self, slug: str, platform: str, platformVersion: str):
        url = self.BASE_URL + self.VERSIONS_ENDPOINT.format(slug=slug)

        params = {
            "limit": 1,
            "channel": "Release",
            "platform": platform,
            "platformVersion": platformVersion,
        }

        response = self.client.get(url, params=params)

        if response.status_code == 404:
            raise errors.McnetError(f"'{slug}' not found on Hangar")

        response.raise_for_status()
        return response.json()

    def resolve(self, slug: str, loader: str, mc_version: str):
        platform = HANGAR[loader]
        data = self._get_versions(slug, platform, mc_version)

        results = data["result"]
        if not results:
            return None

        version = results[0]
        platform_download = version["downloads"].get(platform)

        # Some plugins are hosted off Hangar (GitHub, Patreon, ...): they have
        # no fileInfo, only an external link. We can't download or verify those,
        # so treat them as unavailable.
        if platform_download is None or platform_download["fileInfo"] is None:
            return None

        file_info = platform_download["fileInfo"]

        return Resolved(
            filename=file_info["name"],
            url=platform_download["downloadUrl"],
            hash=file_info["sha256Hash"],
            algorithm="sha256",
            version=version["name"],
        )
