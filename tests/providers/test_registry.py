from typing import Any

import pytest

from mcnet.errors import McnetError
from mcnet.providers.protocols import QueryParams
from mcnet.providers.registry import Providers


class FakeHttp:
    """Canned JSON instead of the network. Satisfies the JsonClient protocol."""

    def __init__(self, payload: Any) -> None:
        self.payload = payload
        self.calls: list[tuple[str, int]] = []

    def get_json(
        self, url: str, params: QueryParams | None = None, ttl: int = 0
    ) -> Any:
        self.calls.append((url, ttl))
        return self.payload


def test_for_source_returns_the_provider() -> None:
    providers = Providers(FakeHttp([]))

    assert providers.for_source("modrinth") is providers.modrinth


def test_for_source_rejects_an_unknown_source() -> None:
    providers = Providers(FakeHttp([]))

    with pytest.raises(McnetError):
        providers.for_source("curseforge")


def test_game_versions_keeps_only_releases() -> None:
    http = FakeHttp(
        [
            {"version": "26.1", "version_type": "release", "date": "", "major": True},
            {"version": "26.2", "version_type": "snapshot", "date": "", "major": False},
            {"version": "26.0", "version_type": "release", "date": "", "major": True},
        ]
    )

    assert Providers(http).modrinth.game_versions() == ["26.1", "26.0"]


def test_game_versions_ask_for_a_day_of_cache() -> None:
    http = FakeHttp([])

    Providers(http).modrinth.game_versions()

    assert http.calls == [("https://api.modrinth.com/v2/tag/game_version", 86400)]
