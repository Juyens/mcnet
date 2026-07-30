class Changes:
    def __init__(self) -> None:
        self.applied: list[str] = []
        self.already: list[str] = []

    def record(self, label: str, current: object, new: object) -> bool:
        """True when new differs from current, filing the right message either way."""
        if new == current:
            self.already.append(f"{label} is already {current}")
            return False

        self.applied.append(f"{label}: {current} -> {new}")
        return True
