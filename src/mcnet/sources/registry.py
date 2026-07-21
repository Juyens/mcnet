from mcnet.sources.modrinth import ModrinthAPI
from mcnet.sources.hangar import HangarAPI
from mcnet import errors

_registry = {
    "modrinth": ModrinthAPI,
    "hangar": HangarAPI,
}
_clients = {}


def get_client(source: str):
    if source not in _registry:
        raise errors.McnetError(f"unknown source: {source}")
    if source not in _clients:
        _clients[source] = _registry[source]()
    return _clients[source]
