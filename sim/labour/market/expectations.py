"""What a person expects a trade to pay in an area, from this year's clearings, and what a stream of
such pay is worth today. Entrants, switchers and migrants all weigh the same numbers.

Expected yearly income in a trade is Harris-Todaro: the hours that find work earn the average wage paid
there (premiums included), the rest earn the outside option (the household's own plot, at subsistence).
"""
import math
from typing import Dict, Mapping, Optional, Tuple

from .records import Clearing, MarketState, YearInputs

ClearingIndex = Mapping[Tuple[str, str], Clearing]   # (area, trade) -> this year's clearing


def index_clearings(clearings) -> Dict[Tuple[str, str], Clearing]:
    return {(each.area, each.trade): each for each in clearings}


def expected_income(state: MarketState, inputs: YearInputs, clearings: ClearingIndex,
                    area: str, trade: str) -> float:
    """Money a year one worker of `trade` in `area` can expect."""
    floor = inputs.subsistence_per_worker_year.get(area, 0.0)
    clearing: Optional[Clearing] = clearings.get((area, trade))
    if clearing is None or clearing.hours_hired <= 0.0:
        if clearing is not None and clearing.vacant_hours > 0.0:
            # employers want hours nobody here offers: the first to arrive is hired at the market wage
            return max(floor, clearing.wage * inputs.hours_per_worker_year)
        return floor
    share = clearing.employment_share if clearing.hours_offered > 0.0 else 1.0
    if clearing.vacant_hours > 0.0:
        share = 1.0
    earned = clearing.average_wage * inputs.hours_per_worker_year
    return share * earned + (1.0 - share) * floor


def annuity_factor(discount_rate: float, years: float) -> float:
    """Present value of one unit a year for `years`, discounted continuously."""
    if years <= 0.0:
        return 0.0
    if discount_rate <= 0.0:
        return years
    return (1.0 - math.exp(-discount_rate * years)) / discount_rate


def present_value(income_per_year: float, discount_rate: float, start_after_years: float,
                  until_years: float) -> float:
    """Value today of `income_per_year` received from `start_after_years` until `until_years`."""
    if until_years <= start_after_years:
        return 0.0
    delay = math.exp(-max(0.0, discount_rate) * start_after_years)
    return income_per_year * delay * annuity_factor(discount_rate, until_years - start_after_years)


def logit_shares(scores: Mapping[str, float], scale: float) -> Dict[str, float]:
    """Choice shares exp(score/scale) normalised, guarded against overflow (log-sum-exp)."""
    if not scores:
        return {}
    if scale <= 0.0:
        best = max(scores.values())
        winners = sorted(key for key, value in scores.items() if value == best)
        return {key: (1.0 / len(winners) if key in winners else 0.0) for key in scores}
    top = max(scores.values())
    weights = {key: math.exp((value - top) / scale) for key, value in scores.items()}
    total = math.fsum(weights.values())
    return {key: weight / total for key, weight in weights.items()}
