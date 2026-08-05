from pathlib import Path
from typing import Any

import pytest

from mcnet.domain.models import Plugin
from mcnet.errors import McnetError
from mcnet.progress import ProgressTask
from mcnet.providers.protocols import QueryParams
from mcnet.providers.registry import Providers
from mcnet.services import jars, plugin, workspace
from mcnet.storage import lock, manifest

URL = "https://modrinth.com/plugin/luckperms"
JAR = "LuckPerms-Bukkit-5.4.140.jar"

PAYLOAD = [
    {
        "version_number": "5.4.140",
        "date_published": "2026-01-01T00:00:00Z",
        "files": [
            {
                "primary": True,
                "filename": JAR,
                "url": "https://cdn.modrinth.com/luckperms.jar",
                "hashes": {"sha1": "aa", "sha512": "4f3c"},
                "size": 3_145_728,
            }
        ],
    }
]


class FakeHttp:
    """A JsonClient that always answers with the same version list."""

    def __init__(self, payload: Any = PAYLOAD) -> None:
        self.payload = payload

    def get_json(
        self, url: str, params: QueryParams | None = None, ttl: int = 0
    ) -> Any:
        return self.payload


class FakeDownloader:
    """A Downloader that writes a stub jar, or fails on command."""

    def __init__(self, error: McnetError | None = None) -> None:
        self.error = error
        self.calls: list[Path] = []

    def download(
        self,
        url: str,
        dest: Path,
        *,
        expected: str,
        algorithm: str,
        task: ProgressTask | None = None,
    ) -> bool:
        if self.error is not None:
            raise self.error

        self.calls.append(dest)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(b"jar")

        return True


def providers(payload: Any = PAYLOAD) -> Providers:
    return Providers(FakeHttp(payload))


@pytest.fixture
def lobby(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.chdir(tmp_path)
    workspace.create(
        "lobby", loader="paper", mc_version="1.21.4", port=25565, root=tmp_path
    )

    return tmp_path / "lobby"


def locked_of(folder: Path):
    return lock.load_lock(folder, manifest.load_manifest(folder))


def test_add_locks_what_the_provider_resolved(lobby: Path) -> None:
    plugin.add(URL, ["lobby"], providers(), FakeDownloader())

    entry = locked_of(lobby).plugins["luckperms"]

    assert entry.source == "modrinth"
    assert entry.version == "5.4.140"
    assert entry.filename == JAR
    assert entry.hash == "4f3c"
    assert entry.algorithm == "sha512"


def test_the_lock_records_what_it_resolved_for(lobby: Path) -> None:
    plugin.add(URL, ["lobby"], providers(), FakeDownloader())

    locked = locked_of(lobby)

    assert locked.loader == "paper"
    assert locked.mc_version == "1.21.4"


def test_add_downloads_into_the_plugins_folder(lobby: Path) -> None:
    downloader = FakeDownloader()

    result = plugin.add(URL, ["lobby"], providers(), downloader)

    assert result.downloaded == ["lobby"]
    assert result.pending == []
    assert downloader.calls == [lobby / jars.PLUGINS_DIR / JAR]
    assert (lobby / jars.PLUGINS_DIR / JAR).exists()


def test_add_without_a_downloader_still_locks(lobby: Path) -> None:
    result = plugin.add(URL, ["lobby"], providers())

    assert result.pending == ["lobby"]
    assert result.downloaded == []
    assert "luckperms" in locked_of(lobby).plugins
    assert not (lobby / jars.PLUGINS_DIR).exists()


def test_a_failed_download_keeps_the_manifest_and_the_lock(lobby: Path) -> None:
    downloader = FakeDownloader(McnetError("hash mismatch for LuckPerms.jar"))

    result = plugin.add(URL, ["lobby"], providers(), downloader)

    assert result.added == ["lobby"]
    assert result.downloaded == []
    assert [failure.name for failure in result.failed] == ["lobby"]
    assert "luckperms" in locked_of(lobby).plugins
    assert manifest.load_manifest(lobby).plugins[0].slug == "luckperms"


def test_an_incompatible_plugin_is_never_locked(lobby: Path) -> None:
    result = plugin.add(URL, ["lobby"], providers([]), FakeDownloader())

    assert [target.name for target in result.incompatible] == ["lobby"]
    assert result.added == []
    assert locked_of(lobby).plugins == {}


def test_remove_drops_the_lock_entry(lobby: Path) -> None:
    plugin.add(URL, ["lobby"], providers(), FakeDownloader())

    plugin.remove("luckperms", ["lobby"])

    assert locked_of(lobby).plugins == {}


def test_remove_deletes_the_jar(lobby: Path) -> None:
    plugin.add(URL, ["lobby"], providers(), FakeDownloader())

    result = plugin.remove("luckperms", ["lobby"])

    assert result.deleted == ["lobby"]
    assert not (lobby / jars.PLUGINS_DIR / JAR).exists()


def test_keeping_the_jar_still_undeclares_the_plugin(lobby: Path) -> None:
    plugin.add(URL, ["lobby"], providers(), FakeDownloader())

    result = plugin.remove("luckperms", ["lobby"], delete_jar=False)

    assert result.removed == ["lobby"]
    assert result.deleted == []
    assert (lobby / jars.PLUGINS_DIR / JAR).exists()
    assert locked_of(lobby).plugins == {}
    assert manifest.load_manifest(lobby).plugins == []


def test_remove_leaves_the_other_jars_alone(lobby: Path) -> None:
    plugin.add(URL, ["lobby"], providers(), FakeDownloader())
    other = lobby / jars.PLUGINS_DIR / "ViaVersion-5.2.1.jar"
    other.write_bytes(b"jar")

    plugin.remove("luckperms", ["lobby"])

    assert other.exists()


def test_a_plugin_that_was_never_downloaded_removes_cleanly(lobby: Path) -> None:
    plugin.add(URL, ["lobby"], providers())

    result = plugin.remove("luckperms", ["lobby"])

    assert result.removed == ["lobby"]
    assert result.deleted == []
    assert result.failed == []
    assert locked_of(lobby).plugins == {}


def test_a_jar_that_will_not_go_stops_the_removal(
    lobby: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plugin.add(URL, ["lobby"], providers(), FakeDownloader())

    def held(_self: Path, *_args: Any, **_kwargs: Any) -> None:
        raise PermissionError(13, "used by another process")

    monkeypatch.setattr(Path, "unlink", held)

    result = plugin.remove("luckperms", ["lobby"])

    assert result.removed == []
    assert [failure.name for failure in result.failed] == ["lobby"]
    assert "luckperms" in locked_of(lobby).plugins
    assert manifest.load_manifest(lobby).plugins[0].slug == "luckperms"


def test_remove_does_not_create_a_lock(lobby: Path) -> None:
    declared = manifest.load_manifest(lobby)
    declared.plugins.append(Plugin(source="modrinth", slug="luckperms"))
    manifest.save_manifest(declared, lobby)

    plugin.remove("luckperms", ["lobby"])

    assert not (lobby / lock.LOCK_NAME).exists()


def test_forget_takes_the_lock_with_it(lobby: Path) -> None:
    plugin.add(URL, ["lobby"], providers(), FakeDownloader())

    workspace.forget(lobby)

    assert not (lobby / lock.LOCK_NAME).exists()
    assert (lobby / jars.PLUGINS_DIR / JAR).exists()
