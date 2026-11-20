"""The wage a market carries from one year to the next under the clearing rules: last year's wage moved a share of the
way to the wage that clears the market (never headed under the least an hour is sold for), by the same share whether
that is a rise or a fall."""
from typing import Optional

from sim.constants import declare

WAGE_SHARE_MOVED_PER_YEAR = declare(
    "WAGE_SHARE_MOVED_PER_YEAR", 0.5, kind="temporary_heuristic", unit="share of the gap to the clearing wage per year",
    source=None, confidence="D",
    retire="Complaints/608: a model of how long a hire holds its pay (the length of a hiring) gives the share",
    why="A wage does not jump to the clearing point in one year: hirings made earlier hold their pay. The share is the "
        "same for a rise and a fall, so a market at its clearing wage stays there and one away from it closes the gap "
        "by a fixed share a year. Not fitted.")


def symmetric_wage(last: Optional[float], goal: float, floor: float, ceiling: float,
                   share: float = WAGE_SHARE_MOVED_PER_YEAR) -> float:
    """The year's wage: where it is headed (`goal`, or `floor` where the goal is under it) in a market with no wage yet,
    else `last` moved `share` of the way there; no higher than `ceiling` where that is above the floor. A wage at or
    above the floor so stays there, and a floor that rose above last year's wage is climbed to by the share a year."""
    headed = max(goal, floor)
    wage = headed if last is None else last + share * (headed - last)
    return min(wage, max(ceiling, floor))
