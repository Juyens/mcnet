from typing import Any

from mcnet.providers.papermc import PaperMcAPI
from mcnet.providers.papermc.api import BUILDS_ENDPOINT, PROJECT_ENDPOINT
from mcnet.providers.protocols import QueryParams


def build(
    number: int, channel: str, *, project: str = "paper", version: str = "1.21.4"
):
    name = f"{project}-{version}-{number}.jar"

    return {
        "id": number,
        "time": "2026-01-01T00:00:00.000Z",
        "channel": channel,
        "downloads": {
            "server:default": {
                "name": name,
                "checksums": {"sha256": f"{number:064x}"},
                "size": 51_437_498,
                "url": f"https://fill-data.papermc.io/v1/objects/{number}/{name}",
            }
        },
    }


class FakeHttp:
    """Answers by URL, so one fake covers the two endpoints the API uses."""

    def __init__(self, routes: dict[str, Any]) -> None:
        self.routes = routes
        self.seen: list[str] = []

    def get_json(
        self, url: str, params: QueryParams | None = None, ttl: int = 0
    ) -> Any:
        self.seen.append(url)

        for tail, payload in self.routes.items():
            if url.endswith(tail):
                return payload

        raise AssertionError(f"unexpected url: {url}")


def builds_route(project: str, version: str) -> str:
    return BUILDS_ENDPOINT.format(project=project, version=version)


def test_the_newest_stable_build_wins() -> None:
    http = FakeHttp(
        {
            builds_route("paper", "1.21.4"): [
                build(232, "ALPHA"),
                build(230, "STABLE"),
                build(228, "STABLE"),
            ]
        }
    )

    resolved = PaperMcAPI(http).resolve(loader="paper", mc_version="1.21.4")

    assert resolved is not None
    assert resolved.version == "1.21.4-230"
    assert resolved.filename == "paper-1.21.4-230.jar"
    assert resolved.algorithm == "sha256"
    assert resolved.size == 51_437_498


def test_folia_falls_back_to_alpha() -> None:
    """Folia has never published anything but ALPHA."""
    http = FakeHttp(
        {
            builds_route("folia", "1.21.4"): [
                build(40, "ALPHA", project="folia"),
                build(41, "ALPHA", project="folia"),
            ]
        }
    )

    resolved = PaperMcAPI(http).resolve(loader="folia", mc_version="1.21.4")

    assert resolved is not None
    assert resolved.version == "1.21.4-41"


def test_a_version_with_no_builds_resolves_to_nothing() -> None:
    http = FakeHttp({builds_route("paper", "1.4.7"): []})

    assert PaperMcAPI(http).resolve(loader="paper", mc_version="1.4.7") is None


def test_velocity_ignores_the_minecraft_version() -> None:
    http = FakeHttp(
        {
            PROJECT_ENDPOINT.format(project="velocity"): {
                "project": {"id": "velocity"},
                "versions": {
                    "4.0.0": ["4.1.0-SNAPSHOT", "4.0.0"],
                    "3.0.0": ["3.5.1", "3.5.0"],
                },
            },
            builds_route("velocity", "4.0.0"): [
                build(6, "STABLE", project="velocity", version="4.0.0")
            ],
            builds_route("velocity", "3.5.1"): [
                build(615, "RECOMMENDED", project="velocity", version="3.5.1")
            ],
        }
    )

    resolved = PaperMcAPI(http).resolve(loader="velocity", mc_version="1.21.4")

    assert resolved is not None
    assert resolved.version == "3.5.1-615"


def test_velocity_settles_for_the_newest_when_nothing_is_recommended() -> None:
    http = FakeHttp(
        {
            PROJECT_ENDPOINT.format(project="velocity"): {
                "project": {"id": "velocity"},
                "versions": {"4.0.0": ["4.0.0"], "3.0.0": ["3.5.1"]},
            },
            builds_route("velocity", "4.0.0"): [
                build(6, "STABLE", project="velocity", version="4.0.0")
            ],
            builds_route("velocity", "3.5.1"): [
                build(615, "STABLE", project="velocity", version="3.5.1")
            ],
        }
    )

    resolved = PaperMcAPI(http).resolve(loader="velocity", mc_version="1.21.4")

    assert resolved is not None
    assert resolved.version == "4.0.0-6"


def test_velocity_sorts_releases_by_number_not_by_text() -> None:
    http = FakeHttp(
        {
            PROJECT_ENDPOINT.format(project="velocity"): {
                "project": {"id": "velocity"},
                "versions": {"3.0.0": ["3.9.0", "3.10.0"]},
            },
            builds_route("velocity", "3.10.0"): [
                build(700, "RECOMMENDED", project="velocity", version="3.10.0")
            ],
        }
    )

    resolved = PaperMcAPI(http).resolve(loader="velocity", mc_version="1.21.4")

    assert resolved is not None
    assert resolved.version == "3.10.0-700"
