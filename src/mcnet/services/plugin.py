from pathlib import Path

from mcnet.domain.models import AnyManifest, LockedJar, Plugin, Resolved
from mcnet.domain.results import AddResult, Failed, Incompatible, RemoveResult
from mcnet.errors import McnetError
from mcnet.providers.protocols import Downloader
from mcnet.providers.registry import Providers
from mcnet.providers.urls import parse_plugin_url
from mcnet.services import jars, workspace
from mcnet.storage import lock, manifest


def add(
    url: str,
    names: list[str],
    providers: Providers,
    downloader: Downloader | None = None,
) -> AddResult:
    """Declare a plugin, lock what it resolved to, and fetch it unless told not to.

    A None downloader means the jar is left for sync, which is also where a
    failed download lands: both leave the manifest and the lock written and
    nothing on disk, so sync cannot tell them apart and does not need to.
    """
    source, slug = parse_plugin_url(url)
    provider = providers.for_source(source)

    result = AddResult(slug=slug)
    targets, result.unknown = workspace.named(names)

    if not targets:
        raise McnetError(
            f"none of those servers exist: {', '.join(result.unknown)}",
            hint="check the spelling with 'mcnet server show'",
        )

    for target in targets:
        declared = manifest.load_manifest(target.folder)

        if _has_plugin(declared, slug):
            result.already.append(target.name)
            continue

        checked = True
        resolved = None

        try:
            resolved = provider.resolve(
                slug, loader=declared.loader, mc_version=declared.mc_version
            )
        except McnetError:
            result.verified = False
            checked = False

        if checked and resolved is None:
            result.incompatible.append(
                Incompatible(
                    name=target.name,
                    loader=declared.loader,
                    mc_version=declared.mc_version,
                )
            )
            continue

        declared.plugins.append(Plugin(source=source, slug=slug))
        manifest.save_manifest(declared, target.folder)
        result.added.append(target.name)

        if resolved is None:
            continue  # unverified: there is nothing to lock or fetch yet

        entry = _record(target.folder, declared, source, slug, resolved)

        if downloader is None:
            result.pending.append(target.name)
            continue

        try:
            jars.install(downloader, jars.plugin_path(target.folder, entry), entry)
        except McnetError as e:
            result.failed.append(Failed(name=target.name, reason=str(e)))
            continue

        result.downloaded.append(target.name)

    return result


def remove(slug: str, names: list[str], *, delete_jar: bool = True) -> RemoveResult:
    """Stop declaring a plugin, and take its jar with it unless told to keep it.

    Keeping the jar leaves a file nothing declares any more, which mcnet will
    not touch again: that is the point of the option, not an oversight.
    """
    targets, unknown = workspace.named(names)

    if not targets:
        raise McnetError(
            f"none of those servers exist: {', '.join(unknown)}",
            hint="check the spelling with 'mcnet server show'",
        )

    result = RemoveResult(slug=slug, unknown=unknown)

    for target in targets:
        declared = manifest.load_manifest(target.folder)

        if not _has_plugin(declared, slug):
            result.missing.append(target.name)
            continue

        locked = lock.load_lock(target.folder, declared)
        entry = locked.plugins.get(slug)

        # Take the jar out first, and give up on this server if it will not go:
        # a plugin still declared with no jar is something sync can fix, while
        # a jar nothing declares is invisible to mcnet from then on.
        if delete_jar and entry is not None:
            try:
                if jars.uninstall(jars.plugin_path(target.folder, entry)):
                    result.deleted.append(target.name)
            except McnetError as e:
                result.failed.append(Failed(name=target.name, reason=str(e)))
                continue

        declared.plugins = [
            plugin for plugin in declared.plugins if plugin.slug != slug
        ]
        manifest.save_manifest(declared, target.folder)

        # Only save when there was something to drop, so a server that never
        # resolved anything does not grow a lock on its way out.
        if locked.plugins.pop(slug, None) is not None:
            lock.save_lock(locked, target.folder)

        result.removed.append(target.name)

    return result


def _record(
    folder: Path,
    declared: AnyManifest,
    source: str,
    slug: str,
    resolved: Resolved,
) -> LockedJar:
    """Write down what the provider resolved, so sync can reproduce it."""
    locked = lock.load_lock(folder, declared)
    entry = LockedJar(
        source=source,
        version=resolved.version,
        filename=resolved.filename,
        hash=resolved.hash,
        algorithm=resolved.algorithm,
        url=resolved.url,
        size=resolved.size,
    )

    locked.loader = declared.loader
    locked.mc_version = declared.mc_version
    locked.plugins[slug] = entry

    lock.save_lock(locked, folder)

    return entry


def _has_plugin(target: AnyManifest, slug: str) -> bool:
    return any(plugin.slug == slug for plugin in target.plugins)
