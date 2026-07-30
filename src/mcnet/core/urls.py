from urllib.parse import urlparse

from mcnet.core.error import McnetError

_HOSTS = {
    "modrinth.com": "modrinth",
    "hangar.papermc.io": "hangar",
}


def parse_plugin_url(url: str) -> tuple[str, str]:
    """Return (source, slug) from a Modrinth or Hangar plugin URL."""
    parsed = urlparse(url)
    host = parsed.netloc.lower()

    if host.startswith("www."):
        host = host[4:]

    source = _HOSTS.get(host)
    if source is None:
        raise McnetError(
            f"unsupported source: {host or url}",
            hint=f"mcnet reads plugins from {', '.join(_HOSTS)}",
        )

    parts = []
    for part in parsed.path.split("/"):
        if part:
            parts.append(part)

    if len(parts) < 2:
        raise McnetError(f"invalid {source} URL: {url}")

    return source, parts[1]
