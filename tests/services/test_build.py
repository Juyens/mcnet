from collections.abc import Callable
from pathlib import Path

import pytest

from mcnet.domain.java import AIKAR, VELOCITY, JavaSettings
from mcnet.domain.models import LockedJar, LockFile
from mcnet.errors import McnetError
from mcnet.services import build, scripts, workspace
from mcnet.storage import eula, lock, manifest, settings

PAPER_JAR = "paper-1.21.4-232.jar"
VELOCITY_JAR = "velocity-3.5.1-615.jar"


class FakeRunner:
    """Writes what a real first start would, without needing a JVM."""

    def __init__(self, breaks: str | None = None) -> None:
        self.breaks = breaks
        self.commands: list[list[str]] = []
        self.stops: list[str] = []

    def boot(
        self,
        folder: Path,
        command: list[str],
        *,
        stop: str,
        watch: Callable[[str], None] | None = None,
    ) -> None:
        self.commands.append(command)
        self.stops.append(stop)

        if self.breaks is not None:
            raise McnetError(self.breaks)

        if watch is not None:
            watch('[21:29:50 INFO]: Preparing level "world"')
            watch('[21:30:01 INFO]: Done (30.925s)! For help, type "help"')

        (folder / "logs").mkdir(exist_ok=True)

        if "--nogui" in command:
            (folder / build.WORLD_NAME).mkdir(exist_ok=True)
        else:
            (folder / settings.VELOCITY_NAME).touch()


def make(root: Path, name: str, loader: str, port: int, jar: str) -> Path:
    workspace.create(name, loader=loader, mc_version="1.21.4", port=port, root=root)
    folder = root / name

    lock.save_lock(
        LockFile(
            loader=loader,
            mc_version="1.21.4",
            server=LockedJar(
                source="papermc",
                version="1.21.4-232",
                filename=jar,
                hash="beef",
                algorithm="sha256",
                url=f"https://example.invalid/{jar}",
            ),
        ),
        folder,
    )

    return folder


@pytest.fixture
def lobby(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.chdir(tmp_path)

    return make(tmp_path, "lobby", "paper", 25566, PAPER_JAR)


@pytest.fixture
def hub(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.chdir(tmp_path)

    return make(tmp_path, "hub", "velocity", 25577, VELOCITY_JAR)


def run(folder: Path, runner: FakeRunner | None = None, **kwargs) -> tuple:
    used = runner or FakeRunner()
    targets, _ = workspace.named([folder.name])
    result = build.build(targets, used, eula_accepted=True, **kwargs)

    return result.servers[0], used


# --- what lands on disk ---------------------------------------------------


def test_the_declared_port_goes_into_server_properties(lobby: Path) -> None:
    run(lobby)

    assert "server-port=25566" in (lobby / settings.PROPERTIES_NAME).read_text()


def test_a_proxy_binds_in_velocity_toml(hub: Path) -> None:
    run(hub)

    assert 'bind = "0.0.0.0:25577"' in (hub / settings.VELOCITY_NAME).read_text()


def test_a_single_key_survives_the_server_filling_the_rest(lobby: Path) -> None:
    """Paper rewrites the file whole; only the declared key is ours to keep."""
    written = lobby / settings.PROPERTIES_NAME
    written.write_text("motd=hand written\nserver-port=1\n", encoding="utf-8")

    run(lobby)

    kept = written.read_text(encoding="utf-8")
    assert "motd=hand written" in kept
    assert "server-port=25566" in kept
    assert "server-port=1" not in kept


def test_both_launchers_are_written(lobby: Path) -> None:
    run(lobby)

    assert (lobby / scripts.SHELL_NAME).exists()
    assert (lobby / scripts.BATCH_NAME).exists()


def test_the_launcher_runs_the_locked_jar(lobby: Path) -> None:
    run(lobby)

    assert PAPER_JAR in (lobby / scripts.SHELL_NAME).read_text()


def test_the_launcher_moves_to_its_own_folder_first(lobby: Path) -> None:
    run(lobby)

    assert 'cd "$(dirname "$0")"' in (lobby / scripts.SHELL_NAME).read_text()
    assert 'cd /d "%~dp0"' in (lobby / scripts.BATCH_NAME).read_text()


def test_git_is_told_to_keep_the_shell_script_lf(lobby: Path) -> None:
    run(lobby)

    assert "start.sh text eol=lf" in (lobby / scripts.GITATTRIBUTES_NAME).read_text()


def test_the_ignore_rules_leave_hand_written_ones_alone(lobby: Path) -> None:
    (lobby / scripts.GITIGNORE_NAME).write_text("mine/\n", encoding="utf-8")

    run(lobby)

    written = (lobby / scripts.GITIGNORE_NAME).read_text(encoding="utf-8")
    assert "mine/" in written
    assert "world*/" in written


def test_running_twice_does_not_repeat_the_rules(lobby: Path) -> None:
    run(lobby)
    first = (lobby / scripts.GITIGNORE_NAME).read_text(encoding="utf-8")

    run(lobby, force=True)

    assert (lobby / scripts.GITIGNORE_NAME).read_text(encoding="utf-8") == first


# --- the jvm command ------------------------------------------------------


def test_a_server_gets_the_server_default(lobby: Path) -> None:
    _, runner = run(lobby)

    assert runner.commands[0][:3] == ["java", "-Xms4G", "-Xmx4G"]
    assert "--nogui" in runner.commands[0]


def test_a_proxy_gets_less_memory_and_no_nogui(hub: Path) -> None:
    _, runner = run(hub)

    assert runner.commands[0][:3] == ["java", "-Xms1G", "-Xmx1G"]
    assert "--nogui" not in runner.commands[0]


def test_nothing_is_tuned_unless_asked(lobby: Path) -> None:
    _, runner = run(lobby)

    assert runner.commands[0] == [
        "java",
        "-Xms4G",
        "-Xmx4G",
        "-jar",
        PAPER_JAR,
        "--nogui",
    ]


@pytest.mark.parametrize(
    ("preset", "expected"), [("aikar", AIKAR), ("velocity", VELOCITY), ("none", ())]
)
def test_a_preset_lands_in_the_command(lobby: Path, preset: str, expected) -> None:
    declared = manifest.load_manifest(lobby)
    declared.java = JavaSettings(memory="8G", flags=preset)
    manifest.save_manifest(declared, lobby)

    _, runner = run(lobby)

    assert runner.commands[0][1:3] == ["-Xms8G", "-Xmx8G"]
    assert runner.commands[0][3 : 3 + len(expected)] == list(expected)


def test_a_list_of_flags_replaces_the_preset(lobby: Path) -> None:
    declared = manifest.load_manifest(lobby)
    declared.java = JavaSettings(flags=["-XX:+UseZGC"])
    manifest.save_manifest(declared, lobby)

    _, runner = run(lobby)

    assert runner.commands[0] == [
        "java",
        "-Xms4G",
        "-Xmx4G",
        "-XX:+UseZGC",
        "-jar",
        PAPER_JAR,
        "--nogui",
    ]


def test_a_proxy_is_stopped_with_its_own_word(hub: Path) -> None:
    _, runner = run(hub)

    assert runner.stops == [build.PROXY_STOP]


# --- the eula -------------------------------------------------------------


def test_accepting_writes_the_file(lobby: Path) -> None:
    run(lobby)

    assert eula.accepted(lobby)


def test_a_proxy_never_needs_one(hub: Path) -> None:
    run(hub)

    assert not (hub / eula.EULA_NAME).exists()
    assert build.needs_eula(workspace.named(["hub"])[0]) == []


def test_refusing_writes_everything_else_but_does_not_start(lobby: Path) -> None:
    targets, _ = workspace.named(["lobby"])
    runner = FakeRunner()

    report = build.build(targets, runner, eula_accepted=False).servers[0]

    assert report.eula_pending
    assert runner.commands == []
    assert (lobby / scripts.SHELL_NAME).exists()
    assert (lobby / settings.PROPERTIES_NAME).exists()
    assert not (lobby / eula.EULA_NAME).exists()


def test_an_already_accepted_server_is_not_asked_again(lobby: Path) -> None:
    eula.accept(lobby)

    assert build.needs_eula(workspace.named(["lobby"])[0]) == []


# --- starting, or not -----------------------------------------------------


def test_a_generated_server_is_not_started_again(lobby: Path) -> None:
    run(lobby)

    report, runner = run(lobby)

    assert report.skipped
    assert runner.commands == []


def test_force_starts_it_anyway(lobby: Path) -> None:
    run(lobby)

    report, runner = run(lobby, force=True)

    assert report.generated
    assert len(runner.commands) == 1


def test_a_server_that_will_not_start_is_reported(lobby: Path) -> None:
    report, _ = run(lobby, FakeRunner(breaks="the server stopped before it was ready"))

    assert report.problem is not None
    assert not report.generated
    # The files are still there, which is the whole point of doing them first.
    assert (lobby / scripts.SHELL_NAME).exists()


def test_a_server_without_a_jar_says_to_sync(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    workspace.create(
        "bare", loader="paper", mc_version="1.21.4", port=25565, root=tmp_path
    )

    report, runner = run(tmp_path / "bare")

    assert report.problem is not None
    assert "sync" in report.problem
    assert runner.commands == []
