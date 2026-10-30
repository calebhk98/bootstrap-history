"""A societal value weight moved by a tech effect or a values-shifting hazard, held between a floor and a ceiling."""
from sim.constants import declare

VALUE_WEIGHT_FLOOR = declare(
    "VALUE_WEIGHT_FLOOR", -1.0, kind="temporary_heuristic",
    unit="dimensionless (bound on any self.value_weights entry)",
    source=None, confidence="D",
    why="Lower bound any societal value weight (self.value_weights) can "
        "be pushed "
        "to by a tech effect or a values-shifting hazard - symmetric "
        "with a weight's own natural -1..1 scale. Not derived from "
        "any model of how far a society's values can actually move.")
VALUE_WEIGHT_CEILING = declare(
    "VALUE_WEIGHT_CEILING", 1.5, kind="temporary_heuristic",
    unit="dimensionless (bound on any self.value_weights entry)",
    source=None, confidence="D",
    why="Upper bound any societal value weight can be pushed to - "
        "asymmetric with VALUE_WEIGHT_FLOOR, allowing a weight to be "
        "reinforced somewhat past its natural 1.0 ceiling by repeated "
        "tech effects. Tuned, not derived.")


def shifted(before: float, delta: float, floor: float, ceiling: float) -> float:
    """`before` plus `delta`, no lower than `floor` and no higher than `ceiling`."""
    return max(floor, min(ceiling, before + delta))
