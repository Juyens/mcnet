from mcnet import errors
from mcnet.sources.baseApi import BaseApi
from mcnet.sources.hangar import HangarAPI
from mcnet.sources.modrinth import ModrinthAPI

_registry = {
    "modrinth": ModrinthAPI,
    "hangar": HangarAPI,
}
_clients = {}


def get_client(source: str) -> BaseApi:
    if source not in _registry:
        raise errors.McnetError(f"unknown source: {source}")
    if source not in _clients:
        _clients[source] = _registry[source]()
    return _clients[source]
