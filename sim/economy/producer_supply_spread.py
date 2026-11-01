"""The spread of workplace costs inside one producer, derived from a short-run supply elasticity."""

import math
from statistics import NormalDist

_STANDARD_NORMAL = NormalDist()


def spread_for_elasticity(elasticity: float, working_share: float) -> float:
    """The log-normal cost spread at which output responds to price with `elasticity` where `working_share` of
    the workplaces work. With share = Phi(z), z = (log(price / cost) + spread^2 / 2) / spread, the elasticity of
    the share to price is pdf(z) / (share * spread)."""
    score = _STANDARD_NORMAL.inv_cdf(working_share)
    return _STANDARD_NORMAL.pdf(score) / (working_share * elasticity)


def spread_at_break_even(elasticity: float) -> float:
    """The spread whose elasticity is `elasticity` where revenue equals the producer's mean cost, so the median
    workplace sits half a spread below the revenue (the elasticity falls as the spread widens: bisection)."""
    low, high = 1e-6, 1e3
    for _ in range(200):
        middle = 0.5 * (low + high)
        score = middle / 2.0
        at_middle = _STANDARD_NORMAL.pdf(score) / (_STANDARD_NORMAL.cdf(score) * middle)
        if at_middle > elasticity:
            low = middle
        else:
            high = middle
    return 0.5 * (low + high)
