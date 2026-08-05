from collections.abc import Callable
from pathlib import Path

from mcnet.domain import java, loaders
from mcnet.domain.models import AnyManifest, LockFile, Target
from mcnet.domain.results import BuildResult, ServerBuild
from mcnet.errors import McnetError
from mcnet.process import Runner
from mcnet.services import scripts
from mcnet.storage import eula, lock, manifest, settings

WORLD_NAME = "world"

STOP_COMMAND = "stop"

PROXY_STOP = "shutdown"


def needs_eula(targets: list[Target]) -> list[Target]:
    """The servers still waiting on an answer. Proxies never need one."""
    return [
        target
        for target in targets
        if not loaders.is_proxy(_loader_of(target)) and not eula.accepted(target.folder)
    ]


def build(
    targets: list[Target],
    runner: Runner,
    *,
    eula_accepted: bool = False,
    force: bool = False,
    watch: Callable[[str, str], None] | None = None,
) -> BuildResult:
    """Make each folder runnable: settings, launchers, and a first start.

    Everything that is only a file gets written even when Java is missing or
    too old, so what you are left with still runs once you install it. The
    boot is the last step for the same reason.
    """
    result = BuildResult()

    for target in targets:
        result.servers.append(_build_one(target, runner, eula_accepted, force, watch))

    return result


def _build_one(
    target: Target,
    runner: Runner,
    eula_accepted: bool,
    force: bool,
    watch: Callable[[str, str], None] | None,
) -> ServerBuild:
    declared = manifest.load_manifest(target.folder)
    locked = lock.load_lock(target.folder, declared)
    report = ServerBuild(name=target.name)
    proxy = loaders.is_proxy(declared.loader)

    settings.set_port(target.folder, declared.port, proxy=proxy)
    report.written.append(settings.VELOCITY_NAME if proxy else settings.PROPERTIES_NAME)

    if not proxy:
        if eula_accepted or eula.accepted(target.folder):
            eula.accept(target.folder)
            report.written.append(eula.EULA_NAME)
        else:
            report.eula_pending = True

    _write_scripts(target, declared, locked, report)
    report.written.extend(path.name for path in scripts.ignore(target.folder))

    if report.eula_pending:
        return report

    if not force and _already_generated(target.folder, proxy):
        report.skipped = True
        return report

    _boot(target, declared, locked, runner, proxy, report, watch)

    return report


def _write_scripts(
    target: Target,
    declared: AnyManifest,
    locked: LockFile,
    report: ServerBuild,
) -> None:
    if locked.server is None:
        report.problem = "no server jar yet, run 'mcnet sync' first"
        return

    runtime = java.runtime(declared.java, declared.loader)
    written = scripts.write(
        target.folder,
        runtime,
        locked.server.filename,
        nogui=java.takes_nogui(declared.loader),
    )

    report.written.extend(path.name for path in written)


def _boot(
    target: Target,
    declared: AnyManifest,
    locked: LockFile,
    runner: Runner,
    proxy: bool,
    report: ServerBuild,
    watch: Callable[[str, str], None] | None,
) -> None:
    if locked.server is None:
        return

    runtime = java.runtime(declared.java, declared.loader)
    command = runtime.command(
        locked.server.filename, nogui=java.takes_nogui(declared.loader)
    )

    try:
        runner.boot(
            target.folder,
            command,
            stop=PROXY_STOP if proxy else STOP_COMMAND,
            needs_java=java.required(declared.loader, declared.mc_version),
            watch=None if watch is None else lambda line: watch(target.name, line),
        )
    except McnetError as e:
        report.problem = str(e)
        return

    report.generated = True


def _already_generated(folder: Path, proxy: bool) -> bool:
    """Whether a previous run left this folder with what a start produces."""
    if proxy:
        return (folder / settings.VELOCITY_NAME).exists() and (folder / "logs").exists()

    return (folder / WORLD_NAME).exists()


def _loader_of(target: Target) -> str:
    return manifest.load_manifest(target.folder).loader
