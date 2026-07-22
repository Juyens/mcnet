from mcnet.core import errors
from mcnet.providers.base import BaseApi
from mcnet.providers.hangar import HangarAPI
from mcnet.providers.modrinth import ModrinthAPI

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
