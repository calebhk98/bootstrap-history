"""The interest rate the economy remembers after a year's lending (rule_sets.py): what plans charge capital and tied-up
coin at, and where next year's lenders start from. The year's loans are struck at the rate that cleared them either
way. Under the search rules the cleared rate is remembered whole; under the clearing rules last year's rate moves a
share of the way to it, as a wage does (`sim.labour.market.wage_step`), so one year in which a few borrowers bid the
rate up does not reprice every run and every plant in the economy."""
from typing import Optional

from sim.constants import declare

RATE_SHARE_MOVED_PER_YEAR = declare(
    "RATE_SHARE_MOVED_PER_YEAR", 0.5, kind="temporary_heuristic", unit="share of the gap to the year's cleared rate per year",
    source=None, confidence="D",
    retire="Complaints/473: the share of the credit outstanding that is struck anew in a year gives it",
    why="Loans struck in earlier years hold their rate, so what credit costs the economy moves with the share of it that "
        "is new. No source found for the share; it is set equal to the wage's (WAGE_SHARE_MOVED_PER_YEAR). Not fitted.")


def the_cleared_rate(_last: Optional[float], cleared: float) -> float:
    """The rate the year's lending cleared at, whole."""
    return cleared


def toward_the_cleared_rate(last: Optional[float], cleared: float, share: float = RATE_SHARE_MOVED_PER_YEAR) -> float:
    """`last` moved `share` of the way to `cleared`; `cleared` where no rate was remembered."""
    return cleared if last is None else last + share * (cleared - last)
