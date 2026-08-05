from typing import Self

from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    SpinnerColumn,
    TaskID,
    TextColumn,
    TimeRemainingColumn,
)

from mcnet.cli.render import log
from mcnet.progress import NullTask, ProgressTask

OVERALL = "downloading"

BAR_WIDTH = 24


class _Bar:
    """One file's row. Rich guards its own state, so threads share this safely."""

    def __init__(self, progress: Progress, task: TaskID, overall: TaskID) -> None:
        self._progress = progress
        self._task = task
        self._overall = overall

    def advance(self, amount: int) -> None:
        self._progress.advance(self._task, amount)

    def done(self) -> None:
        # Finished rows leave, so syncing 500 jars never shows more than the
        # workers actually running, with the overall counter on top.
        self._progress.remove_task(self._task)
        self._progress.advance(self._overall, 1)


class RichSink:
    """A bar per download in flight, with one counter over the lot."""

    def __init__(self) -> None:
        console = log.console()

        self._progress = Progress(
            SpinnerColumn(),
            TextColumn("{task.description}"),
            BarColumn(bar_width=BAR_WIDTH),
            DownloadColumn(),
            TimeRemainingColumn(),
            console=console,
            # Piped output would fill with escape codes nobody reads.
            disable=not console.is_terminal,
            transient=True,
        )
        self._overall: TaskID | None = None

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_: object) -> None:
        self.finish()

    def start(self, jobs: int) -> None:
        self._progress.start()
        self._overall = self._progress.add_task(OVERALL, total=jobs)

    def task(self, label: str, total: int | None) -> ProgressTask:
        if self._overall is None:
            return NullTask()

        return _Bar(
            self._progress,
            self._progress.add_task(label, total=total),
            self._overall,
        )

    def finish(self) -> None:
        if self._overall is None:
            return

        self._progress.stop()
        self._overall = None
