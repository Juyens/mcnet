from mcnet.domain.models import Plugin, Target
from mcnet.domain.results import AddResult, Incompatible, RemoveResult
from mcnet.errors import McnetError
from mcnet.providers.registry import Providers
from mcnet.providers.urls import parse_plugin_url
from mcnet.storage import discovery, manifest
from mcnet.storage.manifest import AnyManifest


def add(url: str, names: list[str], providers: Providers) -> AddResult:
    source, slug = parse_plugin_url(url)
    provider = providers.for_source(source)

    result = AddResult(slug=slug)
    targets, result.unknown = _split_targets(names)

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

        compatible = True

        try:
            compatible = (
                provider.resolve(
                    slug, loader=declared.loader, mc_version=declared.mc_version
                )
                is not None
            )
        except McnetError:
            result.verified = False

        if not compatible:
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

    return result


def remove(slug: str, names: list[str]) -> RemoveResult:
    targets, unknown = _split_targets(names)

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

        declared.plugins = [
            plugin for plugin in declared.plugins if plugin.slug != slug
        ]
        manifest.save_manifest(declared, target.folder)
        result.removed.append(target.name)

    return result


def _split_targets(names: list[str]) -> tuple[list[Target], list[str]]:
    targets, unknown = [], []

    for name in names:
        folder = discovery.find(name)

        if folder is None:
            unknown.append(name)
        else:
            targets.append(Target(name, folder))

    return targets, unknown


def _has_plugin(target: AnyManifest, slug: str) -> bool:
    return any(plugin.slug == slug for plugin in target.plugins)
