from mcnet.domain.models import AddResult, Incompatible, Plugin
from mcnet.errors import McnetError
from mcnet.providers.registry import Providers
from mcnet.providers.urls import parse_plugin_url
from mcnet.storage import discovery, manifest
from mcnet.storage.manifest import AnyManifest


def add(url: str, names: list[str], providers: Providers) -> AddResult:
    source, slug = parse_plugin_url(url)
    provider = providers.for_source(source)

    result = AddResult(slug=slug)
    targets = []

    for name in names:
        folder = discovery.find(name)

        if folder is None:
            result.unknown.append(name)
        else:
            targets.append((name, folder))

    if not targets:
        raise McnetError(
            f"none of those servers exist: {', '.join(result.unknown)}",
            hint="check the spelling, or create them with 'mcnet server create'",
        )

    for name, folder in targets:
        target = manifest.load_manifest(folder)

        if _has_plugin(target, slug):
            result.already.append(name)
            continue

        compatible = True

        try:
            compatible = (
                provider.resolve(
                    slug, loader=target.loader, mc_version=target.mc_version
                )
                is not None
            )
        except McnetError:
            result.verified = False

        if not compatible:
            result.incompatible.append(
                Incompatible(
                    name=name, loader=target.loader, mc_version=target.mc_version
                )
            )
            continue

        target.plugins.append(Plugin(source=source, slug=slug))
        manifest.save_manifest(target, folder)
        result.added.append(name)

    return result


def _has_plugin(target: AnyManifest, slug: str) -> bool:
    return any(plugin.slug == slug for plugin in target.plugins)
