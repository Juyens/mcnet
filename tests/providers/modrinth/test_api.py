from typing import Any

from mcnet.core.types import QueryParams
from mcnet.providers.modrinth.api import ModrinthAPI


class FakeHttp:
    """Stands in for Http: returns canned data and records what was asked for."""

    def __init__(self, data: Any) -> None:
        self._data = data
        self.calls: list[tuple[str, int]] = []

    def get_json(
        self,
        url: str,
        params: QueryParams | None = None,
        ttl: int = 0,
    ) -> Any:
        self.calls.append((url, ttl))
        return self._data


def test_game_version_returns_release_names() -> None:
    http = FakeHttp(
        [
            {"version": "26.2", "version_type": "release", "date": "", "major": True},
            {"version": "26.3-snapshot-1", "version_type": "snapshot", "date": "", "major": False},
        ]
    )

    assert ModrinthAPI(http).game_version() == ["26.2"]


def test_game_version_calls_the_tag_endpoint_with_a_day_of_cache() -> None:
    http = FakeHttp([])

    ModrinthAPI(http).game_version()

    url, ttl = http.calls[0]
    assert url == "https://api.modrinth.com/v2/tag/game_version"
    assert ttl == 86400
