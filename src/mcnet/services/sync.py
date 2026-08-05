from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path

from mcnet import hashing
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
from mcnet.storage import lock, manifest
from mcnet.storage.cache import JarCache

SERVER_SOURCE = "papermc"

# Enough to keep a connection busy without being rude to anyone's CDN.
DEFAULT_WORKERS = 8


@dataclass(frozen=True)
class Job:
    """One jar to fetch, and the report it answers to."""

    report: ServerSync
    path: Path
    entry: LockedJar


def sync(
    targets: list[Target],
    providers: Providers,
    downloader: Downloader,
    cache: JarCache,
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

    _fetch_all(jobs, downloader, cache, workers, sink or NullSink())

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
    jobs: list[Job],
    downloader: Downloader,
    cache: JarCache,
    workers: int,
    sink: ProgressSink,
) -> None:
    """Fetch each distinct jar once, then put copies wherever they belong.

    A network of five paper servers declares the same plugin five times, so
    the work is keyed by hash rather than by job: the pool fetches the unique
    set into the cache, and every job is served from there.

    Workers touch nothing shared, and the reports are filled afterwards in the
    order asked, so two runs print the same thing even though the downloads
    finish in whatever order they please.
    """
    outcomes: dict[int, tuple[bool, str | None]] = {}
    wanted: list[tuple[int, Job]] = []

    for index, job in enumerate(jobs):
        if hashing.file_matches(job.path, job.entry.hash, job.entry.algorithm):
            outcomes[index] = (False, None)
        else:
            wanted.append((index, job))

    if wanted:
        failures = _fill_cache(wanted, downloader, cache, workers, sink)
        _place(wanted, cache, failures, outcomes)

    _file_outcomes(jobs, outcomes)


def _fill_cache(
    wanted: list[tuple[int, Job]],
    downloader: Downloader,
    cache: JarCache,
    workers: int,
    sink: ProgressSink,
) -> dict[str, str]:
    """Get every distinct jar into the cache, reporting what would not come."""
    unique: dict[str, LockedJar] = {}

    for _, job in wanted:
        unique.setdefault(job.entry.hash, job.entry)

    failures: dict[str, str] = {}
    sink.start(len(unique))

    try:
        with ThreadPoolExecutor(max_workers=min(workers, len(unique))) as pool:
            running = {
                pool.submit(_fetch_one, downloader, cache, entry, sink): digest
                for digest, entry in unique.items()
            }

            for future in as_completed(running):
                failure = future.result()

                if failure is not None:
                    failures[running[future]] = failure
    finally:
        sink.finish()

    return failures


def _fetch_one(
    downloader: Downloader, cache: JarCache, entry: LockedJar, sink: ProgressSink
) -> str | None:
    task = sink.task(entry.filename, entry.size)

    try:
        jars.install(downloader, cache.path(entry), entry, task)
    except McnetError as e:
        return str(e)
    finally:
        task.done()

    return None


def _place(
    wanted: list[tuple[int, Job]],
    cache: JarCache,
    failures: dict[str, str],
    outcomes: dict[int, tuple[bool, str | None]],
) -> None:
    for index, job in wanted:
        failure = failures.get(job.entry.hash)

        if failure is not None:
            outcomes[index] = (False, failure)
            continue

        try:
            cache.take(job.entry, job.path)
        except McnetError as e:
            outcomes[index] = (False, str(e))
            continue

        outcomes[index] = (True, None)


def _file_outcomes(
    jobs: list[Job], outcomes: dict[int, tuple[bool, str | None]]
) -> None:
    for index, job in enumerate(jobs):
        fetched, failure = outcomes[index]

        if failure is not None:
            job.report.failed.append(Failed(name=job.entry.filename, reason=failure))
        elif fetched:
            job.report.downloaded.append(job.entry.filename)
        else:
            job.report.current.append(job.entry.filename)


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
