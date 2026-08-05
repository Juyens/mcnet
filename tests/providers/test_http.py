import hashlib
from collections.abc import Callable
from pathlib import Path

import httpx
import pytest

from mcnet.errors import McnetError
from mcnet.providers.http import PART_SUFFIX, Http

URL = "https://cdn.modrinth.com/luckperms.jar"

BODY = b"not really a jar, but it hashes just the same"
DIGEST = hashlib.sha512(BODY).hexdigest()

type Handler = Callable[[httpx.Request], httpx.Response]


def serving(body: bytes = BODY, status: int = 200) -> Handler:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(status, content=body)

    return handler


def unreachable(_request: httpx.Request) -> httpx.Response:
    raise httpx.ConnectError("no route to host")


def make_http(tmp_path: Path, handler: Handler) -> Http:
    return Http(
        "mcnet-tests",
        cache_dir=tmp_path / "cache",
        transport=httpx.MockTransport(handler),
    )


def fetch(http: Http, dest: Path, expected: str = DIGEST) -> bool:
    return http.download(URL, dest, expected=expected, algorithm="sha512")


def test_a_download_lands_with_the_right_bytes(tmp_path: Path) -> None:
    dest = tmp_path / "lobby" / "plugins" / "luckperms.jar"

    assert fetch(make_http(tmp_path, serving()), dest) is True
    assert dest.read_bytes() == BODY


def test_a_file_that_already_matches_is_left_alone(tmp_path: Path) -> None:
    dest = tmp_path / "luckperms.jar"
    dest.write_bytes(BODY)

    assert fetch(make_http(tmp_path, unreachable), dest) is False


def test_a_file_with_the_wrong_bytes_is_replaced(tmp_path: Path) -> None:
    dest = tmp_path / "luckperms.jar"
    dest.write_bytes(b"an older build")

    assert fetch(make_http(tmp_path, serving()), dest) is True
    assert dest.read_bytes() == BODY


def test_a_hash_mismatch_is_reported(tmp_path: Path) -> None:
    dest = tmp_path / "luckperms.jar"

    with pytest.raises(McnetError, match="hash mismatch"):
        fetch(make_http(tmp_path, serving(b"something else")), dest)


def test_a_hash_mismatch_leaves_nothing_behind(tmp_path: Path) -> None:
    dest = tmp_path / "luckperms.jar"

    with pytest.raises(McnetError):
        fetch(make_http(tmp_path, serving(b"something else")), dest)

    assert not dest.exists()
    assert not dest.with_name(dest.name + PART_SUFFIX).exists()


def test_a_mismatch_does_not_destroy_the_previous_jar(tmp_path: Path) -> None:
    dest = tmp_path / "luckperms.jar"
    dest.write_bytes(b"an older build")

    with pytest.raises(McnetError):
        fetch(make_http(tmp_path, serving(b"something else")), dest)

    assert dest.read_bytes() == b"an older build"


def test_a_missing_file_is_reported(tmp_path: Path) -> None:
    with pytest.raises(McnetError, match="not found"):
        fetch(make_http(tmp_path, serving(b"", 404)), tmp_path / "luckperms.jar")


def test_a_server_error_is_reported(tmp_path: Path) -> None:
    with pytest.raises(McnetError, match="503"):
        fetch(make_http(tmp_path, serving(b"", 503)), tmp_path / "luckperms.jar")


def test_an_unreachable_host_is_reported(tmp_path: Path) -> None:
    with pytest.raises(McnetError, match="cannot reach"):
        fetch(make_http(tmp_path, unreachable), tmp_path / "luckperms.jar")


def test_an_unknown_algorithm_is_reported(tmp_path: Path) -> None:
    with pytest.raises(McnetError, match="unknown hash algorithm"):
        make_http(tmp_path, serving()).download(
            URL, tmp_path / "luckperms.jar", expected=DIGEST, algorithm="sha0"
        )
