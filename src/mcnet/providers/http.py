import hashlib
import json
import time
from pathlib import Path
from typing import Any

import httpx

from mcnet.errors import McnetError
from mcnet.providers.protocols import QueryParams

RETRY_STATUS = frozenset({429, 500, 502, 503, 504})


class Http:
    def __init__(self, user_agent: str, cache_dir: Path) -> None:
        self._client = httpx.Client(
            headers={"User-Agent": user_agent}, timeout=20, follow_redirects=True
        )
        self._cache_dir = cache_dir

    def get_json(
        self, url: str, params: QueryParams | None = None, ttl: int = 0
    ) -> Any:
        cached = self._read_cache(url, params, ttl)
        if cached is not None:
            return cached

        response = self._request(url, params)

        if response.status_code == 404:
            raise McnetError(f"not found: {url}")

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise McnetError(f"{e.response.status_code} from {url}") from e

        try:
            data = response.json()
        except ValueError as e:
            raise McnetError(f"invalid response from {url}") from e

        if ttl > 0:
            self._write_cache(url, params, data)

        return data

    def close(self) -> None:
        self._client.close()

    def _cache_path(self, url: str, params: QueryParams | None) -> Path:
        key = url + json.dumps(dict(params or {}), sort_keys=True)
        digest = hashlib.sha256(key.encode()).hexdigest()[:16]
        return self._cache_dir / f"{digest}.json"

    def _read_cache(self, url: str, params: QueryParams | None, ttl: int) -> Any | None:
        if ttl <= 0:
            return None

        path = self._cache_path(url, params)
        if not path.exists():
            return None

        if time.time() - path.stat().st_mtime > ttl:
            return None

        return json.loads(path.read_text(encoding="utf-8"))

    def _request(
        self, url: str, params: QueryParams | None, attempts: int = 3
    ) -> httpx.Response:
        response: httpx.Response | None = None
        error: httpx.RequestError | None = None

        for attempt in range(attempts):
            if attempt:
                time.sleep(2 ** (attempt - 1))

            try:
                response = self._client.get(url, params=params)
            except httpx.RequestError as e:
                error = e
                continue

            if response.status_code not in RETRY_STATUS:
                return response

        if response is not None:
            return response

        raise McnetError(f"cannot reach {url}") from error

    def _write_cache(self, url: str, params: QueryParams | None, data: Any) -> None:
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._cache_path(url, params).write_text(json.dumps(data), encoding="utf-8")
