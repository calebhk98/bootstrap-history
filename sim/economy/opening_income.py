"""The opening's household income, settled with the demand it pays for.

An opening that gives every worker a full year of work at the opening wage pays out far more than the
households spend (their needs are met well short of it) and far more than the producers sized to what they
spend can pay: the first year's realised income is a fraction of the opening figure and the wage falls to
meet the hours nobody hires. Here income is the value of what the opening makes. At prices that equal costs
the factor payments (wages, rent, the plant's charge) add up to the value of final demand, so the income the
households receive is the income that pays for the demand producers are sized to: a fixed point of income,
demand and prices, found by iterating from the full-employment ceiling.
"""
import math
from typing import Callable, Dict, Mapping

from .households_cohort import Cohort
from .types import GoodId, TileId

OPENING_INCOME_PASSES = 60     # a numerical bound: demand saturates with income, so the iteration stops well before it
OPENING_INCOME_TOLERANCE = 1e-9


def value_of(final_by_tile: Mapping[TileId, Mapping[GoodId, float]], prices: Mapping[GoodId, float]) -> float:
    """Money value of a final demand at the prices given."""
    return math.fsum(quantity * prices.get(good, 0.0)
                     for demand in final_by_tile.values() for good, quantity in demand.items())


def settled_income_per_head(ceiling: float, people: float, demand_at: Callable[[float], float]) -> float:
    """Income per head at which the value of final demand (`demand_at(income per head)`) equals the income
    paid, found from the `ceiling` (full employment at the opening wage) downward."""
    if people <= 0.0:
        return 0.0
    income = ceiling
    for _pass in range(OPENING_INCOME_PASSES):
        paid = min(ceiling, demand_at(income) / people)
        if abs(paid - income) <= OPENING_INCOME_TOLERANCE * max(paid, 1e-300):
            return paid
        income = paid
    return income


def with_income_per_head(cohorts: Mapping[str, Cohort], per_head: float) -> Dict[str, Cohort]:
    """The cohorts with each class's last year's income at its ownership share of `per_head` over the people."""
    by_tile: Dict[TileId, float] = {}
    for cohort in cohorts.values():
        by_tile[cohort.tile] = by_tile.get(cohort.tile, 0.0) + cohort.people
    return {agent_id: _with_income(cohort, per_head, by_tile[cohort.tile]) for agent_id, cohort in cohorts.items()}


def _with_income(cohort: Cohort, per_head: float, tile_people: float) -> Cohort:
    from .replaced import replaced
    return replaced(cohort, last_year_income=cohort.ownership_share * tile_people * per_head)


def working_share(recipe, prices: Mapping[GoodId, float], wages: Mapping[str, float]) -> float:
    """Share of a producer's plant that works at the opening prices: only the workplaces whose own cost the
    revenue covers do (producers.share_working), so a producer sized to the runs households' demand needs
    has that much more plant than it works. A recipe the prices make unprofitable counts as working in full
    (the opening sizes it to the demand, and the first year's plan finds out)."""
    from . import producers, unit_cost
    variable = unit_cost.variable_cost_per_run(recipe, prices, wages)
    if not math.isfinite(variable) or variable <= 0.0:
        return 1.0
    share = producers.share_working(unit_cost.revenue_per_run(recipe, prices), variable)
    return share if share > 0.0 else 1.0
