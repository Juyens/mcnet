import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import httpx
from rich.progress import Progress

from mcnet.core import errors
from mcnet.core.models import DownloadTask


def download(url: str, hash: str, algorithm: str, filename: str, dest: Path):
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".tmp")
    hash_algorithm = hashlib.new(algorithm)

    with httpx.stream("GET", url, follow_redirects=True) as response:
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise errors.McnetError(f"{e.response.status_code} for {filename}") from e

        with tmp.open("wb") as file:
            for chunk in response.iter_bytes():
                file.write(chunk)
                hash_algorithm.update(chunk)

    if hash_algorithm.hexdigest() != hash:
        tmp.unlink()
        raise errors.McnetError(f"hash mismatch for {filename}")

    tmp.replace(dest)


def download_all(tasks: list[DownloadTask]) -> tuple[list, dict]:
    downloaded = []
    failed = {}

    with Progress() as progress:
        bar = progress.add_task("Downloading", total=len(tasks))

        with ThreadPoolExecutor(max_workers=6) as pool:
            futures = {}
            for task in tasks:
                future = pool.submit(
                    download,
                    task.url,
                    task.hash,
                    task.algorithm,
                    task.filename,
                    task.dest,
                )
                futures[future] = task

            for future in as_completed(futures):
                task = futures[future]
                try:
                    future.result()
                    downloaded.append(task.key)
                except (errors.McnetError, httpx.HTTPError) as e:
                    failed[task.key] = f"download failed: {e}"
                progress.update(bar, advance=1)

    return downloaded, failed
