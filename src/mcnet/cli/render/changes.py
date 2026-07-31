from mcnet.services.servers import FieldChange


def applied(change: FieldChange) -> str:
    return f"{change.label}: {change.old} -> {change.new}"


def unchanged(change: FieldChange) -> str:
    return f"{change.label} is already {change.old}"
