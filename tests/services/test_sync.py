import hashlib
import random
import threading
import time
from pathlib import Path
from typing import Any

import pytest

from mcnet import hashing
from mcnet.domain.models import Plugin
from mcnet.errors import McnetError
from mcnet.progress import NullTask, ProgressTask
from mcnet.providers.protocols import QueryParams
from mcnet.providers.registry import Providers
from mcnet.services import jars, sync, workspace
from mcnet.storage import lock, manifest
from mcnet.storage.cache import JarCache

# Stand-in jars with real digests, so sync runs its own hashing rather than
# trusting a fake to say what is already in place.
BLOBS: dict[str, bytes] = {}


def _publish(filename: str, algorithm: str) -> str:
    body = f"pretend this is {filename}".encode()
    digest = hashlib.new(algorithm, body).hexdigest()
    BLOBS[digest] = body

    return digest


PAPER_JAR = "paper-1.21.4-232.jar"
PAPER_HASH = _publish(PAPER_JAR, "sha256")

PAPER_BUILDS = [
    {
        "id": 232,
        "time": "2026-01-01T00:00:00.000Z",
        "channel": "STABLE",
        "downloads": {
            "server:default": {
                "name": PAPER_JAR,
                "checksums": {"sha256": PAPER_HASH},
                "size": 51_437_498,
                "url": "https://fill-data.papermc.io/v1/objects/x/" + PAPER_JAR,
            }
        },
    }
]


def jar_of(slug: str) -> str:
    return f"{slug}-1.0.0.jar"


def versions_of(slug: str) -> list[dict[str, Any]]:
    """Each slug gets its own bytes, so hashes differ the way they really do."""
    filename = jar_of(slug)

    return [
        {
            "version_number": "1.0.0",
            "date_published": "2026-01-01T00:00:00Z",
            "files": [
                {
                    "primary": True,
                    "filename": filename,
                    "url": "https://cdn.modrinth.com/" + filename,
                    "hashes": {"sha1": "aa", "sha512": _publish(filename, "sha512")},
                    "size": 1_490_252,
                }
            ],
        }
    ]


PLUGIN_JAR = jar_of("luckperms")

MODRINTH_VERSIONS = versions_of("luckperms")


def slug_of(url: str) -> str:
    return url.split("/project/")[1].split("/")[0]


class FakeHttp:
    """Routes by URL so one fake serves PaperMC and Modrinth at once."""

    def get_json(
        self, url: str, params: QueryParams | None = None, ttl: int = 0
    ) -> Any:
        if "papermc.io" in url:
            return PAPER_BUILDS

        if "modrinth.com" in url:
            return versions_of(slug_of(url))

        raise AssertionError(f"unexpected url: {url}")


class FakeDownloader:
    """Counts calls apart from real fetches, the way Http tells them apart."""

    def __init__(self) -> None:
        self.calls: list[Path] = []
        self.fetched = 0

    def download(
        self,
        url: str,
        dest: Path,
        *,
        expected: str,
        algorithm: str,
        task: ProgressTask | None = None,
    ) -> bool:
        self.calls.append(dest)

        if hashing.file_matches(dest, expected, algorithm):
            return False

        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(BLOBS[expected])
        self.fetched += 1

        return True


def providers() -> Providers:
    return Providers(FakeHttp())


def cache() -> JarCache:
    """Rooted in the test's own cwd, so nothing touches the real cache."""
    return JarCache(Path("_cache"))


@pytest.fixture
def network(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.chdir(tmp_path)
    workspace.create(
        "lobby", loader="paper", mc_version="1.21.4", port=25565, root=tmp_path
    )

    return tmp_path


def declare(folder: Path, slug: str, source: str = "modrinth") -> None:
    declared = manifest.load_manifest(folder)
    declared.plugins.append(Plugin(source=source, slug=slug))
    manifest.save_manifest(declared, folder)


def run(name: str | None = None, root: Path | None = None) -> Any:
    downloader = FakeDownloader()
    result = sync.sync(sync.targets(name, root), providers(), downloader, cache())

    return result, downloader


# --- picking what to sync -------------------------------------------------


def test_a_named_server_syncs_only_itself(network: Path) -> None:
    workspace.create(
        "hub", loader="velocity", mc_version="1.21.4", port=25577, root=network
    )

    result, _ = run("lobby")

    assert [server.name for server in result.servers] == ["lobby"]


def test_no_name_takes_every_server_in_order(network: Path) -> None:
    for name in ("survival", "creative"):
        workspace.create(
            name, loader="paper", mc_version="1.21.4", port=25566, root=network
        )

    result, _ = run()

    assert [server.name for server in result.servers] == [
        "creative",
        "lobby",
        "survival",
    ]


def test_an_unmanaged_folder_is_skipped(network: Path) -> None:
    (network / "notes").mkdir()

    result, _ = run()

    assert [server.name for server in result.servers] == ["lobby"]


@pytest.mark.usefixtures("network")
def test_a_name_that_is_not_there_is_reported() -> None:
    with pytest.raises(McnetError, match="nothing named 'ghost'"):
        sync.targets("ghost")


def test_an_empty_folder_is_reported(tmp_path: Path) -> None:
    with pytest.raises(McnetError, match="no servers are managed here"):
        sync.targets(None, tmp_path)


# --- what lands on disk ---------------------------------------------------


def test_the_server_jar_lands_beside_the_manifest(network: Path) -> None:
    result, _ = run("lobby")

    assert (network / "lobby" / PAPER_JAR).exists()
    assert PAPER_JAR in result.servers[0].downloaded


def test_the_server_jar_is_written_to_the_lock(network: Path) -> None:
    run("lobby")

    locked = lock.load_lock(
        network / "lobby", manifest.load_manifest(network / "lobby")
    )

    assert locked.server is not None
    assert locked.server.filename == PAPER_JAR
    assert locked.server.version == "1.21.4-232"


def test_declared_plugins_are_resolved_and_fetched(network: Path) -> None:
    declare(network / "lobby", "luckperms")

    result, _ = run("lobby")

    assert (network / "lobby" / jars.PLUGINS_DIR / PLUGIN_JAR).exists()
    assert sorted(result.servers[0].downloaded) == sorted([PAPER_JAR, PLUGIN_JAR])


def test_a_second_sync_downloads_nothing(network: Path) -> None:
    declare(network / "lobby", "luckperms")
    run("lobby")

    result, _ = run("lobby")

    assert result.servers[0].downloaded == []
    assert sorted(result.servers[0].current) == sorted([PAPER_JAR, PLUGIN_JAR])


def test_a_fresh_clone_needs_no_provider(network: Path) -> None:
    """With everything locked, sync fetches without asking any API."""
    declare(network / "lobby", "luckperms")
    run("lobby")

    for jar in (network / "lobby").rglob("*.jar"):
        jar.unlink()

    class Refuses:
        def get_json(self, *args: Any, **kwargs: Any) -> Any:
            raise AssertionError("sync should not have called an API")

    downloader = FakeDownloader()
    result = sync.sync(sync.targets("lobby"), Providers(Refuses()), downloader, cache())

    assert sorted(result.servers[0].downloaded) == sorted([PAPER_JAR, PLUGIN_JAR])


# --- sweeping -------------------------------------------------------------


def test_a_plugin_no_longer_declared_is_swept(network: Path) -> None:
    declare(network / "lobby", "luckperms")
    run("lobby")

    declared = manifest.load_manifest(network / "lobby")
    declared.plugins = []
    manifest.save_manifest(declared, network / "lobby")

    result, _ = run("lobby")

    assert result.servers[0].removed == [PLUGIN_JAR]
    assert not (network / "lobby" / jars.PLUGINS_DIR / PLUGIN_JAR).exists()


def test_a_jar_mcnet_never_placed_survives(network: Path) -> None:
    run("lobby")
    stray = network / "lobby" / jars.PLUGINS_DIR / "EssentialsX.jar"
    stray.parent.mkdir(parents=True, exist_ok=True)
    stray.write_bytes(b"placed by hand")

    result, _ = run("lobby")

    assert stray.exists()
    assert result.servers[0].removed == []


def test_changing_the_version_relocks_and_sweeps(network: Path) -> None:
    run("lobby")
    workspace.edit(network / "lobby", mc_version="1.21.5")

    result, _ = run("lobby")

    locked = lock.load_lock(
        network / "lobby", manifest.load_manifest(network / "lobby")
    )
    assert locked.mc_version == "1.21.5"
    assert result.servers[0].failed == []


# --- what goes wrong ------------------------------------------------------


def test_a_plugin_that_resolves_to_nothing_is_reported(network: Path) -> None:
    declare(network / "lobby", "luckperms")

    class NoVersions(FakeHttp):
        def get_json(
            self, url: str, params: QueryParams | None = None, ttl: int = 0
        ) -> Any:
            return PAPER_BUILDS if "papermc.io" in url else []

    downloader = FakeDownloader()
    result = sync.sync(
        sync.targets("lobby"), Providers(NoVersions()), downloader, cache()
    )
    report = result.servers[0]

    assert [failure.name for failure in report.failed] == ["luckperms"]
    assert "no paper version for 1.21.4" in report.failed[0].reason
    assert result.failed


def test_the_server_jar_still_lands_when_a_plugin_fails(network: Path) -> None:
    declare(network / "lobby", "luckperms")

    class NoVersions(FakeHttp):
        def get_json(
            self, url: str, params: QueryParams | None = None, ttl: int = 0
        ) -> Any:
            return PAPER_BUILDS if "papermc.io" in url else []

    result = sync.sync(
        sync.targets("lobby"), Providers(NoVersions()), FakeDownloader(), cache()
    )

    assert (network / "lobby" / PAPER_JAR).exists()
    assert result.servers[0].downloaded == [PAPER_JAR]


@pytest.mark.usefixtures("network")
def test_an_unreachable_api_is_reported_not_raised() -> None:
    class Down:
        def get_json(self, *args: Any, **kwargs: Any) -> Any:
            raise McnetError("cannot reach https://fill.papermc.io/v3")

    result = sync.sync(
        sync.targets("lobby"), Providers(Down()), FakeDownloader(), cache()
    )

    assert [failure.name for failure in result.servers[0].failed] == ["paper"]
    assert result.failed


# --- fetching in parallel -------------------------------------------------


class SlowDownloader:
    """Records overlap, so a pool can be told apart from a queue."""

    def __init__(self, workers: int) -> None:
        self.barrier = threading.Barrier(workers, timeout=5)
        self.peak = 0
        self._live = 0
        self._guard = threading.Lock()

    def download(
        self,
        url: str,
        dest: Path,
        *,
        expected: str,
        algorithm: str,
        task: ProgressTask | None = None,
    ) -> bool:
        with self._guard:
            self._live += 1
            self.peak = max(self.peak, self._live)

        self.barrier.wait()

        with self._guard:
            self._live -= 1

        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(BLOBS[expected])

        if task is not None:
            task.advance(len(BLOBS[expected]))

        return True


def test_downloads_really_overlap(network: Path) -> None:
    for slug in ("luckperms", "viaversion", "vault"):
        declare(network / "lobby", slug)

    downloader = SlowDownloader(workers=4)

    sync.sync(sync.targets("lobby"), providers(), downloader, cache(), workers=4)

    assert downloader.peak == 4


def test_a_single_worker_still_fetches_everything(network: Path) -> None:
    declare(network / "lobby", "luckperms")

    result = sync.sync(
        sync.targets("lobby"), providers(), FakeDownloader(), cache(), workers=1
    )

    assert sorted(result.servers[0].downloaded) == sorted([PAPER_JAR, PLUGIN_JAR])


def test_results_follow_the_plan_not_the_finish_order(network: Path) -> None:
    """Whatever order the pool completes in, the report reads the same."""
    for slug in ("luckperms", "viaversion", "vault"):
        declare(network / "lobby", slug)

    seen = []

    for _ in range(4):
        for jar in (network / "lobby").rglob("*.jar"):
            jar.unlink()

        result = sync.sync(
            sync.targets("lobby"), providers(), ShuffledDownloader(), cache(), workers=8
        )
        seen.append(result.servers[0].downloaded)

    assert all(order == seen[0] for order in seen)


class ShuffledDownloader:
    """Finishes in an order unrelated to the one it was asked in."""

    def download(
        self,
        url: str,
        dest: Path,
        *,
        expected: str,
        algorithm: str,
        task: ProgressTask | None = None,
    ) -> bool:
        time.sleep(random.uniform(0, 0.02))
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(BLOBS[expected])

        return True


def test_the_sink_is_told_about_every_job(network: Path) -> None:
    declare(network / "lobby", "luckperms")

    sink = RecordingSink()
    sync.sync(sync.targets("lobby"), providers(), FakeDownloader(), cache(), sink=sink)

    assert sink.jobs == 2
    assert sorted(sink.labels) == sorted([PAPER_JAR, PLUGIN_JAR])
    assert sink.finished


class RecordingSink:
    def __init__(self) -> None:
        self.jobs = 0
        self.labels: list[str] = []
        self.finished = False
        self._guard = threading.Lock()

    def start(self, jobs: int) -> None:
        self.jobs = jobs

    def task(self, label: str, total: int | None) -> ProgressTask:
        with self._guard:
            self.labels.append(label)

        return NullTask()

    def finish(self) -> None:
        self.finished = True


# --- the cache ------------------------------------------------------------


def three_paper_servers(network: Path) -> None:
    for name in ("survival", "creative"):
        workspace.create(
            name, loader="paper", mc_version="1.21.4", port=25566, root=network
        )

    for name in ("lobby", "survival", "creative"):
        declare(network / name, "luckperms")


def test_a_shared_jar_is_fetched_once_for_the_whole_network(network: Path) -> None:
    three_paper_servers(network)

    downloader = FakeDownloader()
    result = sync.sync(sync.targets(None), providers(), downloader, cache())

    # Three servers, two jars each, but only two distinct artifacts.
    assert sum(len(server.downloaded) for server in result.servers) == 6
    assert len(downloader.calls) == 2


def test_every_server_still_gets_its_own_copy(network: Path) -> None:
    three_paper_servers(network)

    sync.sync(sync.targets(None), providers(), FakeDownloader(), cache())

    for name in ("lobby", "survival", "creative"):
        assert (network / name / PAPER_JAR).exists()
        assert (network / name / jars.PLUGINS_DIR / PLUGIN_JAR).exists()


def test_a_warm_cache_needs_no_download_at_all(network: Path) -> None:
    three_paper_servers(network)
    shared = cache()
    sync.sync(sync.targets(None), providers(), FakeDownloader(), shared)

    for jar in network.rglob("*.jar"):
        jar.unlink()

    downloader = FakeDownloader()
    result = sync.sync(sync.targets(None), providers(), downloader, shared)

    assert sum(len(server.downloaded) for server in result.servers) == 6
    assert downloader.fetched == 0


def test_a_jar_that_will_not_download_is_reported_for_every_server(
    network: Path,
) -> None:
    three_paper_servers(network)

    class Broken(FakeDownloader):
        def download(
            self,
            url: str,
            dest: Path,
            *,
            expected: str,
            algorithm: str,
            task: ProgressTask | None = None,
        ) -> bool:
            if PLUGIN_JAR in url:
                raise McnetError(f"hash mismatch for {PLUGIN_JAR}")

            return super().download(
                url, dest, expected=expected, algorithm=algorithm, task=task
            )

    result = sync.sync(sync.targets(None), providers(), Broken(), cache())

    assert all(len(server.failed) == 1 for server in result.servers)
    assert all(server.downloaded == [PAPER_JAR] for server in result.servers)


def test_the_progress_counts_distinct_jars_not_jobs(network: Path) -> None:
    three_paper_servers(network)

    sink = RecordingSink()
    sync.sync(sync.targets(None), providers(), FakeDownloader(), cache(), sink=sink)

    assert sink.jobs == 2
    assert sorted(sink.labels) == sorted([PAPER_JAR, PLUGIN_JAR])
