from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path

from mcnet.domain.models import (
    AnyManifest,
    LockedJar,
    LockFile,
    Plugin,
    Resolved,
    Target,
)
from mcnet.domain.results import Failed, ServerSync, SyncResult
from mcnet.errors import McnetError
from mcnet.progress import NullSink, ProgressSink
from mcnet.providers.protocols import Downloader
from mcnet.providers.registry import Providers
from mcnet.services import jars
from mcnet.storage import discovery, lock, manifest

SERVER_SOURCE = "papermc"

# Enough to keep a connection busy without being rude to anyone's CDN.
DEFAULT_WORKERS = 8


@dataclass(frozen=True)
class Job:
    """One jar to fetch, and the report it answers to."""

    report: ServerSync
    path: Path
    entry: LockedJar


def targets(name: str | None, root: Path | None = None) -> list[Target]:
    """The server asked for, or every one managed here."""
    if name is not None:
        return [Target(name, discovery.locate(name, root))]

    folders = discovery.managed(root)

    if not folders:
        raise McnetError(
            "no servers are managed here",
            hint="create one with 'mcnet server create', or cd into your network",
        )

    return [Target(folder.name, folder) for folder in folders]


def sync(
    targets: list[Target],
    providers: Providers,
    downloader: Downloader,
    *,
    workers: int = DEFAULT_WORKERS,
    sink: ProgressSink | None = None,
) -> SyncResult:
    """Put on disk what every manifest declares, resolving whatever is missing.

    Two phases on purpose. Planning resolves and writes every lock, so the
    intent is on disk before a byte is fetched; fetching then runs as one pool
    across the whole network, because a hundred plugins one after another is
    the slow part and they do not depend on each other.
    """
    result = SyncResult()
    jobs = []

    for target in targets:
        report = ServerSync(name=target.name)
        result.servers.append(report)
        jobs.extend(_plan(target, providers, report))

    _fetch_all(jobs, downloader, workers, sink or NullSink())

    return result


def _plan(target: Target, providers: Providers, report: ServerSync) -> list[Job]:
    """Settle what this server should have, and say what is left to fetch."""
    declared = manifest.load_manifest(target.folder)
    locked = lock.load_lock(target.folder, declared)

    # Whatever the lock knew before this run. Anything that falls out of it is
    # ours to delete; anything else in the folder was not put there by mcnet.
    was = locked.filenames()

    if not locked.matches(declared.loader, declared.mc_version):
        locked = LockFile(loader=declared.loader, mc_version=declared.mc_version)

    # The manifest is the intent, so anything it no longer declares leaves the
    # lock here: that is what makes its jar fall into the sweep below.
    _prune(declared, locked)

    jobs = []

    _plan_server(target, declared, locked, providers, report, jobs)

    for plugin in declared.plugins:
        _plan_plugin(target, declared, locked, plugin, providers, report, jobs)

    _sweep(target.folder, was - locked.filenames(), report)

    lock.save_lock(locked, target.folder)

    return jobs


def _prune(declared: AnyManifest, locked: LockFile) -> None:
    slugs = {plugin.slug for plugin in declared.plugins}

    locked.plugins = {
        slug: entry for slug, entry in locked.plugins.items() if slug in slugs
    }


def _plan_server(
    target: Target,
    declared: AnyManifest,
    locked: LockFile,
    providers: Providers,
    report: ServerSync,
    jobs: list[Job],
) -> None:
    if locked.server is None:
        locked.server = _resolve(
            lambda: providers.for_loader(declared.loader).resolve(
                loader=declared.loader, mc_version=declared.mc_version
            ),
            source=SERVER_SOURCE,
            label=declared.loader,
            missing=f"no {declared.loader} build for {declared.mc_version}",
            report=report,
        )

    if locked.server is not None:
        path = jars.server_path(target.folder, locked.server)
        jobs.append(Job(report=report, path=path, entry=locked.server))


def _plan_plugin(
    target: Target,
    declared: AnyManifest,
    locked: LockFile,
    plugin: Plugin,
    providers: Providers,
    report: ServerSync,
    jobs: list[Job],
) -> None:
    entry = locked.plugins.get(plugin.slug)

    if entry is None:
        entry = _resolve(
            lambda: providers.for_source(plugin.source).resolve(
                plugin.slug, loader=declared.loader, mc_version=declared.mc_version
            ),
            source=plugin.source,
            label=plugin.slug,
            missing=f"no {declared.loader} version for {declared.mc_version}",
            report=report,
        )

        if entry is None:
            return

        locked.plugins[plugin.slug] = entry

    jobs.append(
        Job(report=report, path=jars.plugin_path(target.folder, entry), entry=entry)
    )


def _resolve(
    ask: Callable[[], Resolved | None],
    *,
    source: str,
    label: str,
    missing: str,
    report: ServerSync,
) -> LockedJar | None:
    """Ask a provider for a jar, filing whatever went wrong instead of raising."""
    try:
        resolved = ask()
    except McnetError as e:
        report.failed.append(Failed(name=label, reason=str(e)))
        return None

    if resolved is None:
        report.failed.append(Failed(name=label, reason=missing))
        return None

    return LockedJar(
        source=source,
        version=resolved.version,
        filename=resolved.filename,
        hash=resolved.hash,
        algorithm=resolved.algorithm,
        url=resolved.url,
        size=resolved.size,
    )


def _fetch_all(
    jobs: list[Job], downloader: Downloader, workers: int, sink: ProgressSink
) -> None:
    """Fetch every job at once, then file the outcomes in the order asked.

    Workers touch nothing shared: each returns its outcome and the reports are
    filled in afterwards, so a run always prints the same thing twice even
    though the downloads finish in whatever order they please.
    """
    if not jobs:
        return

    sink.start(len(jobs))
    outcomes: dict[int, tuple[bool, str | None]] = {}

    try:
        with ThreadPoolExecutor(max_workers=min(workers, len(jobs))) as pool:
            running = {
                pool.submit(_fetch_one, downloader, job, sink): index
                for index, job in enumerate(jobs)
            }

            for future in as_completed(running):
                outcomes[running[future]] = future.result()
    finally:
        sink.finish()

    for index, job in enumerate(jobs):
        fetched, failure = outcomes[index]

        if failure is not None:
            job.report.failed.append(Failed(name=job.entry.filename, reason=failure))
        elif fetched:
            job.report.downloaded.append(job.entry.filename)
        else:
            job.report.current.append(job.entry.filename)


def _fetch_one(
    downloader: Downloader, job: Job, sink: ProgressSink
) -> tuple[bool, str | None]:
    task = sink.task(job.entry.filename, job.entry.size)

    try:
        return jars.install(downloader, job.path, job.entry, task), None
    except McnetError as e:
        return False, str(e)
    finally:
        task.done()


def _sweep(folder: Path, stale: set[str], report: ServerSync) -> None:
    """Drop the jars this sync replaced, and nothing else.

    Only files the previous lock accounted for are fair game, so a jar the
    user dropped in by hand, or one kept with 'plugin remove --keep-jar',
    survives instead of vanishing on the next run.
    """
    for filename in sorted(stale):
        for path in (folder / filename, folder / jars.PLUGINS_DIR / filename):
            try:
                if jars.uninstall(path):
                    report.removed.append(filename)
            except McnetError as e:
                report.failed.append(Failed(name=filename, reason=str(e)))
