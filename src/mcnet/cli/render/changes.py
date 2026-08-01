from mcnet.domain.changes import FieldChange


def applied_line(change: FieldChange) -> str:
    return f"{change.label}: {change.old} -> {change.new}"


def unchanged_line(change: FieldChange) -> str:
    return f"{change.label} is already {change.old}"
