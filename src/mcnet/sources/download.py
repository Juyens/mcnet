import hashlib
import httpx
from pathlib import Path

from mcnet import errors
from mcnet.sources.baseApi import Resolved


def download(resolved: Resolved, dest: Path):
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".tmp")

    hash_algorithm = hashlib.new(resolved.algorithm)

    with httpx.stream("GET", resolved.url, follow_redirects=True) as response:
        response.raise_for_status()

        with tmp.open("wb") as file:
            for chunk in response.iter_bytes():
                file.write(chunk)
                hash_algorithm.update(chunk)

        if hash_algorithm.hexdigest() != resolved.hash:
            tmp.unlink()
            raise errors.McnetError(f"hash mismatch for {resolved.filename}")

        tmp.replace(dest)
