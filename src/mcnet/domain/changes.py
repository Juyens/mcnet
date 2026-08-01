from dataclasses import dataclass, field


@dataclass(frozen=True)
class FieldChange:
    label: str
    old: object
    new: object


@dataclass
class ChangeSet:
    applied: list[FieldChange] = field(default_factory=list)
    unchanged: list[FieldChange] = field(default_factory=list)
    needs_sync: bool = False

    def record(
        self, label: str, old: object, new: object, *, syncs: bool = False
    ) -> bool:
        """True when new differs from old, filing the change either way."""
        if old == new:
            self.unchanged.append(FieldChange(label, old, new))
            return False

        self.applied.append(FieldChange(label, old, new))

        if syncs:
            self.needs_sync = True

        return True
