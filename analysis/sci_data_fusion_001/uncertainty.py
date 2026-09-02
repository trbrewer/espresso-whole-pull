FIELDS = ("statistic", "estimand", "scale", "replicate_unit", "state", "observation_operator")


def compatible(left: dict, right: dict) -> bool:
    return all(left.get(field) is not None and left.get(field) == right.get(field) for field in FIELDS)


def combine(*_args, **_kwargs):
    raise RuntimeError("SCI-DATA-FUSION-001 freezes no numerical uncertainty-combination rule")

