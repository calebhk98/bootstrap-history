"""The hired household work a household counts on (rule_sets.py).

A household plans the hours of household work it hires a share of the way from last year's figure to what it wants
(`households_work.adjusted_hired_hours`), does the rest itself and keeps those hours back from the labour it sells.
Under the search rules last year's figure is last year's plan and it counts on the whole of this year's plan. Where
few servants are to be had the plan then climbs year after year while nobody comes, and the hours it "freed" are
sold. Under the clearing rules the figure is what it was actually served (its plan less the hours of the need it went
without, which the close keeps), and it counts on no more than that, so it still bids for more servants than it had
and keeps the hours for the work they have not yet done."""
from typing import Optional, Tuple


def as_planned(hired_last_year: float, _unmet_last_year: float) -> Tuple[float, Optional[float]]:
    """(the hours next year's plan starts from, the most it counts on being served: None for whatever it plans): last year's plan."""
    return hired_last_year, None


def as_served(hired_last_year: float, unmet_last_year: float) -> Tuple[float, Optional[float]]:
    """(the hours next year's plan starts from, the most it counts on being served): both the hours it was served last
    year, its plan less the hours it went without, never under nothing."""
    served = max(0.0, hired_last_year - max(0.0, unmet_last_year))
    return served, served
