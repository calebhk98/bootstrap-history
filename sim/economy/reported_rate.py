"""The market rate the engine reads: the loan-weighted average of the year's clearings, held under the nominal ceiling.

The base rate in the economy's memory is the marginal rate of the last clearing, what planners discount at. A caller that asks
"the market rate" means what a loan was struck at on average, so it reads this one.
"""
from typing import Optional

from sim.world import capital_market


def reported_rate(opening_rate: float, average_rate: Optional[float], remembered_rate: Optional[float],
                  expected_inflation: float) -> Optional[float]:
    """The year's loan-weighted average rate, else the remembered base rate when no clearing lent, held under the ceiling on
    the real rate plus the inflation lenders expect; None when the economy holds neither."""
    rate = average_rate if average_rate is not None else remembered_rate
    return None if rate is None else capital_market.bounded_rate(opening_rate, rate, expected_inflation)
