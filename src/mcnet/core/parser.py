from mcnet import errors
from urllib.parse import urlparse


def parse_list(value: str) -> list[str]:
    result = []
    for item in value.split(","):
        item = item.strip()
        if item:
            result.append(item)
    return result


def parse_plugin_url(url: str):
    parsed = urlparse(url)
    host = parsed.netloc.lower()

    if host.startswith("www."):
        host = host[4:]

    parts = []

    for part in parsed.path.split("/"):
        if part:
            parts.append(part)

    if host == "modrinth.com":
        if len(parts) < 2:
            raise errors.McnetError(f"invalid Modrinth URL: {url}")
        return "modrinth", parts[1]

    if host == "hangar.papermc.io":
        if len(parts) < 2:
            raise errors.McnetError(f"invalid Hangar URL: {url}")
        return "hangar", parts[1]

    raise errors.McnetError(f"unsupported source: {host}")
