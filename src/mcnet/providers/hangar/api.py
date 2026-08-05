from mcnet.domain.loaders import ProxyLoader, ServerLoader
from mcnet.domain.models import Resolved
from mcnet.errors import NotFoundError
from mcnet.providers.hangar import assembler
from mcnet.providers.hangar.endpoints.version import VersionsResource
from mcnet.providers.protocols import JsonClient, Provider

BASE_URL = "https://hangar.papermc.io/api/v1"
ONE_DAY = 86400

VERSIONS_ENDPOINT = "/projects/{slug}/versions"

RELEASE = "Release"

# Hangar sorts by platform rather than by server software, and its PAPER
# platform already covers what Spigot and Bukkit plugins run on.
PLATFORMS = {
    ServerLoader.PAPER: "PAPER",
    ServerLoader.PURPUR: "PAPER",
    ServerLoader.FOLIA: "PAPER",
    ProxyLoader.VELOCITY: "VELOCITY",
}

# Only PAPER is versioned by Minecraft. A VELOCITY plugin declares which
# Velocity it needs, and only to major.minor, so asking by Minecraft version
# matches nothing at all and asking by the exact one ('3.5.1') misses too.
VERSIONED_BY_MINECRAFT = frozenset({"PAPER"})


class HangarAPI(Provider):
    def __init__(self, http: JsonClient) -> None:
        self._http = http

    def resolve(self, slug: str, *, loader: str, mc_version: str) -> Resolved | None:
        platform = PLATFORMS.get(loader)

        if platform is None:
            return None

        url = BASE_URL + VERSIONS_ENDPOINT.format(slug=slug)
        params: dict[str, str | int] = {
            "limit": 1,
            "channel": RELEASE,
            "platform": platform,
        }

        if platform in VERSIONED_BY_MINECRAFT:
            params["platformVersion"] = mc_version

        try:
            data: VersionsResource = self._http.get_json(url, params, ttl=ONE_DAY)
        except NotFoundError:
            return None

        return assembler.to_resolved(data, platform=platform)
