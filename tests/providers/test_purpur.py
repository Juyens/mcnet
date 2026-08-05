from typing import Any

from mcnet.errors import NotFoundError
from mcnet.providers.protocols import QueryParams
from mcnet.providers.purpur import PurpurAPI

LATEST = {
    "project": "purpur",
    "version": "1.21.4",
    "build": "2416",
    "result": "SUCCESS",
    "timestamp": 1744500645780,
    "md5": "e3832b46efa4a2a56d31bc7ce26df6f0",
}


class FakeHttp:
    def __init__(self, payload: Any) -> None:
        self.payload = payload

    def get_json(
        self, url: str, params: QueryParams | None = None, ttl: int = 0
    ) -> Any:
        if isinstance(self.payload, Exception):
            raise self.payload

        return self.payload


def test_the_latest_build_resolves() -> None:
    resolved = PurpurAPI(FakeHttp(LATEST)).resolve(loader="purpur", mc_version="1.21.4")

    assert resolved is not None
    assert resolved.filename == "purpur-1.21.4-2416.jar"
    assert resolved.version == "1.21.4-2416"
    assert resolved.hash == LATEST["md5"]
    assert resolved.algorithm == "md5"
    assert resolved.url.endswith("/purpur/1.21.4/2416/download")


def test_purpur_publishes_no_size() -> None:
    """The API says nothing about it, so the lock records nothing either."""
    resolved = PurpurAPI(FakeHttp(LATEST)).resolve(loader="purpur", mc_version="1.21.4")

    assert resolved is not None
    assert resolved.size is None


def test_a_failed_build_is_not_offered() -> None:
    broken = LATEST | {"result": "FAILURE"}

    assert (
        PurpurAPI(FakeHttp(broken)).resolve(loader="purpur", mc_version="1.21.4")
        is None
    )


def test_an_unsupported_version_resolves_to_nothing() -> None:
    http = FakeHttp(NotFoundError("not found"))

    assert PurpurAPI(http).resolve(loader="purpur", mc_version="1.4.7") is None
