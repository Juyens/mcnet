from mcnet.domain.models import Incompatible


def incompatible_line(target: Incompatible) -> str:
    return f"no {target.loader} version for {target.mc_version}"
