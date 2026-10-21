"""A societal value weight moved by a tech effect or a values-shifting hazard, held between a floor and a ceiling."""


def shifted(before: float, delta: float, floor: float, ceiling: float) -> float:
    """`before` plus `delta`, no lower than `floor` and no higher than `ceiling`."""
    return max(floor, min(ceiling, before + delta))
