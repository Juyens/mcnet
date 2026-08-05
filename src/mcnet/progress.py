from typing import Protocol


class ProgressTask(Protocol):
    """One file being fetched. Handed out by a sink, one per download."""

    def advance(self, amount: int) -> None: ...

    def done(self) -> None: ...


class ProgressSink(Protocol):
    """Where progress goes. Handles, not one bar, because downloads overlap."""

    def start(self, jobs: int) -> None: ...

    def task(self, label: str, total: int | None) -> ProgressTask: ...

    def finish(self) -> None: ...


class NullTask:
    def advance(self, amount: int) -> None:
        return None

    def done(self) -> None:
        return None


class NullSink:
    """What the services use when nobody is watching, so they never branch."""

    def start(self, jobs: int) -> None:
        return None

    def task(self, label: str, total: int | None) -> ProgressTask:
        return NullTask()

    def finish(self) -> None:
        return None
