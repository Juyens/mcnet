from pathlib import Path

import pytest

from mcnet.core.error import McnetError
from mcnet.core.models import Manifest
from mcnet.core.validation import is_version_shape, name_problem
from mcnet.manifest import save_manifest, server_folder


@pytest.mark.parametrize(
    "value",
    ["26.1", "26.1.2", "1.21.4", "1.21.11"],
)
def test_accepts_release_shapes(value: str) -> None:
    assert is_version_shape(value)


@pytest.mark.parametrize(
    "value",
    [
        "",
        "26",
        "26.x",
        "26.1.2.3",
        "1,21",
        "latest",
        "26.3-snapshot-1",
        " 26.1",
    ],
)
def test_rejects_anything_else(value: str) -> None:
    assert not is_version_shape(value)


@pytest.mark.parametrize("value", ["survival", "lobby-2", "mi_red", "s"])
def test_accepts_simple_names(value: str) -> None:
    assert name_problem(value) is None


@pytest.mark.parametrize(
    "value",
    ["", "Survival", "mi server", "-lobby", "surv/ival", "nul", "com1", "a" * 33],
)
def test_rejects_problematic_names(value: str) -> None:
    assert name_problem(value) is not None


@pytest.fixture
def survival() -> Manifest:
    return Manifest(
        loader="paper",
        mc_version="26.1.2",
        port=25565,
    )


def test_finds_a_named_server(tmp_path: Path, survival: Manifest) -> None:
    folder = tmp_path / "survival"
    folder.mkdir()
    save_manifest(survival, folder)

    assert server_folder("survival", root=tmp_path) == folder


def test_fails_when_the_folder_has_no_manifest(tmp_path: Path) -> None:
    (tmp_path / "survival").mkdir()

    with pytest.raises(McnetError):
        server_folder("survival", root=tmp_path)


def test_fails_when_the_folder_does_not_exist(tmp_path: Path) -> None:
    with pytest.raises(McnetError):
        server_folder("survival", root=tmp_path)
