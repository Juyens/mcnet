from pathlib import Path

import pytest

from mcnet.errors import McnetError
from mcnet.services import servers
from mcnet.storage import manifest


def make_lobby(root: Path) -> Path:
    servers.create("lobby", loader="paper", mc_version="1.21.4", port=25565, root=root)

    return root / "lobby"


def test_create_writes_a_manifest(tmp_path: Path) -> None:
    path = servers.create(
        "lobby", loader="paper", mc_version="1.21.4", port=25565, root=tmp_path
    )

    assert path == tmp_path / "lobby" / "mcnet.yaml"

    saved = manifest.load_manifest(tmp_path / "lobby")
    assert saved.loader == "paper"
    assert saved.mc_version == "1.21.4"
    assert saved.port == 25565
    assert saved.plugins == []


def test_create_refuses_an_existing_folder(tmp_path: Path) -> None:
    (tmp_path / "lobby").mkdir()

    with pytest.raises(McnetError):
        servers.create(
            "lobby", loader="paper", mc_version="1.21.4", port=25565, root=tmp_path
        )


def test_locate_rejects_a_folder_without_a_manifest(tmp_path: Path) -> None:
    (tmp_path / "lobby").mkdir()

    with pytest.raises(McnetError):
        servers.locate("lobby", root=tmp_path)


def test_edit_applies_and_persists(tmp_path: Path) -> None:
    folder = make_lobby(tmp_path)

    result = servers.edit(folder, loader="purpur", port=25570)

    assert [change.label for change in result.applied] == ["loader", "port"]
    assert result.unchanged == []

    saved = manifest.load_manifest(folder)
    assert saved.loader == "purpur"
    assert saved.port == 25570


def test_edit_reports_values_that_already_match(tmp_path: Path) -> None:
    folder = make_lobby(tmp_path)

    result = servers.edit(folder, loader="paper")

    assert result.applied == []
    assert [change.label for change in result.unchanged] == ["loader"]


def test_edit_without_options_changes_nothing(tmp_path: Path) -> None:
    folder = make_lobby(tmp_path)

    result = servers.edit(folder)

    assert result.applied == []
    assert result.unchanged == []


def test_a_new_loader_needs_a_sync(tmp_path: Path) -> None:
    folder = make_lobby(tmp_path)

    assert servers.edit(folder, loader="folia").needs_sync


def test_a_new_version_needs_a_sync(tmp_path: Path) -> None:
    folder = make_lobby(tmp_path)

    assert servers.edit(folder, mc_version="1.21.9").needs_sync


def test_a_new_port_does_not_need_a_sync(tmp_path: Path) -> None:
    folder = make_lobby(tmp_path)

    result = servers.edit(folder, port=25570)

    assert result.applied
    assert not result.needs_sync


def test_forget_drops_the_manifest_but_keeps_the_files(tmp_path: Path) -> None:
    folder = make_lobby(tmp_path)
    (folder / "world").mkdir()

    servers.forget(folder)

    assert not (folder / "mcnet.yaml").exists()
    assert (folder / "world").exists()


def test_delete_removes_everything(tmp_path: Path) -> None:
    folder = make_lobby(tmp_path)

    servers.delete(folder)

    assert not folder.exists()


def test_has_world_follows_the_folder(tmp_path: Path) -> None:
    folder = make_lobby(tmp_path)
    assert not servers.has_world(folder)

    (folder / "world").mkdir()
    assert servers.has_world(folder)


def test_declared_plugins_counts_the_manifest(tmp_path: Path) -> None:
    folder = make_lobby(tmp_path)

    assert servers.declared_plugins(folder) == 0
