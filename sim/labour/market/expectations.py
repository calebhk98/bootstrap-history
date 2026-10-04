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


def graduates_coming(state: MarketState, area: str, trade: str, completion_by_band) -> float:
    """People now in training for a trade here who are expected to finish it."""
    total = 0.0
    for cohort in state.trainees.get(area, {}).get(trade, []):
        total += math.fsum(count * chance for count, chance in zip(cohort[1], completion_by_band))
    return total


def income_at_graduation(state: MarketState, inputs: YearInputs, clearings: ClearingIndex, area: str,
                         trade: str, completion_by_band) -> float:
    """What a trade is expected to pay once someone starting its training now has finished.

    Today's premium over the outside option is kept only for the part of today's shortage the people
    already training will not fill (net of those leaving meanwhile): a full workshop of apprentices
    tells the next entrant the shortage will be gone. Without this, entrants answer today's wage, the
    trade gluts a training-length later, and wages cycle from floor to ceiling."""
    now = expected_income(state, inputs, clearings, area, trade)
    clearing: Optional[Clearing] = clearings.get((area, trade))
    floor = inputs.subsistence_per_worker_year.get(area, 0.0)
    if clearing is None or now <= floor:
        return now
    hours = inputs.hours_per_worker_year
    shortage_now = clearing.hours_wanted - clearing.hours_offered
    if shortage_now <= 0.0:
        return now
    years = inputs.trades[trade].training_years
    staying = max(0.0, 1.0 - inputs.attrition_share.get(area, 0.0)) ** years
    supply_then = (clearing.hours_offered * staying
                   + graduates_coming(state, area, trade, completion_by_band) * hours)
    shortage_then = clearing.hours_wanted - supply_then
    remaining = max(0.0, min(1.0, shortage_then / shortage_now))
    return floor + (now - floor) * remaining
