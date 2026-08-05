from typing import Self

from mcnet.providers.http import Http
from mcnet.providers.protocols import Downloader
from mcnet.providers.registry import Providers
from mcnet.storage.cache import JarCache

_USER_AGENT = "juyens/mcnet (joseph.juliuscb@gmail.com)"


class Session:
    """A session is a context manager that provides access to the providers."""

    def __init__(self) -> None:
        self._http = Http(_USER_AGENT)
        self._providers = Providers(self._http)
        self._cache = JarCache()

    @property
    def providers(self) -> Providers:
        return self._providers

    @property
    def downloader(self) -> Downloader:
        """The same client the providers use, narrowed to fetching files."""
        return self._http

    @property
    def cache(self) -> JarCache:
        return self._cache

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_: object) -> None:
        self._http.close()
