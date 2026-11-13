"""An army's readiness: how well drilled and blooded it is against the reference soldier, 1 at best. Drill and battle keep
it up; a year idle wears it down toward a floor. Plain functions of numbers."""
import math

from sim.constants import declare

READINESS_LOSS_PER_IDLE_YEAR = declare(
    "READINESS_LOSS_PER_IDLE_YEAR", 0.1, kind="temporary_heuristic", unit="rate a year, exponent on the readiness above the floor",
    source=None, confidence="D",
    why="How fast an army that does not fight loses its edge in a peace. No source opened gives a decay of drill or "
        "morale; a trained force's skill as labour hours of drill the army line pays for would give it.",
    retire="Complaints/485: unit types, training and morale from the army line's labour")

READINESS_FLOOR = declare(
    "READINESS_FLOOR", 0.5, kind="temporary_heuristic", unit="share of the best readiness",
    source=None, confidence="D",
    why="The least readiness a standing force falls to however long the peace: men who still carry arms and know "
        "the drill. No source opened.",
    retire="Complaints/485: unit types, training and morale from the army line's labour")


def readiness_after_year(readiness: float, fought: bool) -> float:
    """Readiness a year on: a force that fought is blooded and back at its best; an idle one loses a share of what it
    holds above the floor."""
    if fought:
        return 1.0
    held = max(READINESS_FLOOR, min(1.0, readiness))
    return READINESS_FLOOR + (held - READINESS_FLOOR) * math.exp(-READINESS_LOSS_PER_IDLE_YEAR)
