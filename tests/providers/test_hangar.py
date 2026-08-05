from typing import Any

from mcnet.errors import NotFoundError
from mcnet.providers.hangar import HangarAPI
from mcnet.providers.protocols import QueryParams


def download(platform: str, name: str) -> dict[str, Any]:
    return {
        "fileInfo": {
            "name": name,
            "sizeBytes": 744_323,
            "sha256Hash": "7015a7b4",
        },
        "externalUrl": None,
        "downloadUrl": f"https://hangarcdn.papermc.io/plugins/x/{platform}/{name}",
    }


def versions(**downloads: dict[str, Any]) -> dict[str, Any]:
    return {
        "result": [
            {
                "name": "3.5.1",
                "channel": {"name": "Release"},
                "downloads": downloads,
            }
        ]
    }


class FakeHttp:
    def __init__(self, payload: Any) -> None:
        self.payload = payload
        self.params: QueryParams | None = None

    def get_json(
        self, url: str, params: QueryParams | None = None, ttl: int = 0
    ) -> Any:
        self.params = params

        if isinstance(self.payload, Exception):
            raise self.payload

        return self.payload


def test_a_server_plugin_resolves() -> None:
    http = FakeHttp(versions(PAPER=download("PAPER", "GSit-3.5.1.jar")))

    resolved = HangarAPI(http).resolve("GSit", loader="paper", mc_version="1.21.4")

    assert resolved is not None
    assert resolved.filename == "GSit-3.5.1.jar"
    assert resolved.version == "3.5.1"
    assert resolved.algorithm == "sha256"
    assert resolved.size == 744_323


def test_every_bukkit_flavour_asks_for_the_paper_platform() -> None:
    """Hangar's PAPER already covers what Spigot and Bukkit plugins run on."""
    for loader in ("paper", "purpur", "folia"):
        http = FakeHttp(versions(PAPER=download("PAPER", "GSit-3.5.1.jar")))

        assert HangarAPI(http).resolve("GSit", loader=loader, mc_version="1.21.4")
        assert http.params is not None
        assert http.params["platform"] == "PAPER"


def test_a_server_is_filtered_by_its_minecraft_version() -> None:
    http = FakeHttp(versions(PAPER=download("PAPER", "GSit-3.5.1.jar")))

    HangarAPI(http).resolve("GSit", loader="paper", mc_version="1.21.4")

    assert http.params is not None
    assert http.params["platformVersion"] == "1.21.4"


def test_a_proxy_is_not_filtered_by_the_minecraft_version() -> None:
    """A VELOCITY plugin declares which Velocity it needs, not which MC."""
    http = FakeHttp(versions(VELOCITY=download("VELOCITY", "Maintenance.jar")))

    resolved = HangarAPI(http).resolve(
        "Maintenance", loader="velocity", mc_version="1.21.4"
    )

    assert resolved is not None
    assert http.params is not None
    assert "platformVersion" not in http.params


def test_a_plugin_without_a_build_for_that_platform_resolves_to_nothing() -> None:
    http = FakeHttp(versions(PAPER=download("PAPER", "GSit-3.5.1.jar")))

    assert (
        HangarAPI(http).resolve("GSit", loader="velocity", mc_version="1.21.4") is None
    )


def test_a_plugin_hosted_elsewhere_is_not_offered() -> None:
    """No file to fetch and no hash to check, so it counts as unavailable."""
    elsewhere = {
        "fileInfo": None,
        "externalUrl": "https://github.com/someone/plugin/releases",
        "downloadUrl": None,
    }
    http = FakeHttp(versions(PAPER=elsewhere))

    assert HangarAPI(http).resolve("Thing", loader="paper", mc_version="1.21.4") is None


def test_no_releases_resolves_to_nothing() -> None:
    assert (
        HangarAPI(FakeHttp({"result": []})).resolve(
            "GSit", loader="paper", mc_version="1.21.4"
        )
        is None
    )


def test_an_unknown_project_resolves_to_nothing() -> None:
    http = FakeHttp(NotFoundError("not found"))

    assert HangarAPI(http).resolve("Nope", loader="paper", mc_version="1.21.4") is None


def test_a_loader_hangar_has_no_platform_for_is_skipped() -> None:
    http = FakeHttp(versions())

    assert HangarAPI(http).resolve("GSit", loader="fabric", mc_version="1.21.4") is None
    assert http.params is None
