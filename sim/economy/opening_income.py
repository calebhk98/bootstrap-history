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
from typing import Callable, Dict, Mapping, Tuple

from .households_cohort import Cohort
from .types import GoodId, TileId

OPENING_INCOME_PASSES = 60     # a numerical bound: demand saturates with income, so the iteration stops well before it
OPENING_INCOME_TOLERANCE = 1e-9


def value_of(final_by_tile: Mapping[TileId, Mapping[GoodId, float]], prices: Mapping[GoodId, float]) -> float:
    """Money value of a final demand at the prices given."""
    return math.fsum(quantity * prices.get(good, 0.0)
                     for demand in final_by_tile.values() for good, quantity in demand.items())


def settled_income_per_head(ceiling: float, people: float, demand_at: Callable[[float], Tuple[float, float]]
                            ) -> Tuple[float, float]:
    """(income per head, labour share of it) at which the value of final demand equals the income paid, found
    from the `ceiling` (full employment at the opening wage) downward. `demand_at(income per head)` gives the
    value of the demand that income buys and the share of that value which pays labour."""
    if people <= 0.0:
        return 0.0, 0.0
    income = ceiling
    labour_share = 0.0
    for _pass in range(OPENING_INCOME_PASSES):
        value, labour_share = demand_at(income)
        paid = min(ceiling, value / people)
        if abs(paid - income) <= OPENING_INCOME_TOLERANCE * max(paid, 1e-300):
            return paid, labour_share
        income = paid
    return income, labour_share


def labour_share_of(runs: Mapping[str, float], recipes: Mapping[str, object], wages: Mapping[str, float],
                    value: float) -> float:
    """Share of an output of `value` that the producers of `runs` pay their workers (the rest is rent and the
    plant's charge, which their owners receive); at most one."""
    from . import unit_cost
    bill = math.fsum(count * unit_cost.labour_cost_per_run(recipes[recipe_id], wages) for recipe_id, count in runs.items())
    return min(1.0, bill / value) if value > 0.0 else 0.0


def with_income(cohorts: Mapping[str, Cohort], per_head: float, labour_share: float) -> Dict[str, Cohort]:
    """The cohorts with each class's last year's income: the labour share of the total divided by working people
    (every worker is paid alike), the rest by what each class owns."""
    working: Dict[TileId, float] = {}
    people: Dict[TileId, float] = {}
    for cohort in cohorts.values():
        working[cohort.tile] = working.get(cohort.tile, 0.0) + cohort.working_people
        people[cohort.tile] = people.get(cohort.tile, 0.0) + cohort.people
    from .replaced import replaced
    paid = {}
    for agent_id, cohort in cohorts.items():
        tile_total = per_head * people[cohort.tile]
        worked = cohort.working_people / working[cohort.tile] if working[cohort.tile] > 0.0 else 0.0
        paid[agent_id] = replaced(cohort, last_year_income=tile_total * (
            labour_share * worked + (1.0 - labour_share) * cohort.ownership_share))
    return paid


def working_share(recipe, prices: Mapping[GoodId, float], wages: Mapping[str, float]) -> float:
    """Share of a producer's plant that works at the opening prices: only the workplaces whose own cost the
    revenue covers do (producers.share_working), so a producer sized to the runs households' demand needs
    has that much more plant than it works. A recipe whose revenue does not cover its variable cost at these
    prices counts as working in full (the opening sizes it to the demand, and the first year's plan finds out)."""
    from . import producers, unit_cost
    variable = unit_cost.variable_cost_per_run(recipe, prices, wages)
    revenue = unit_cost.revenue_per_run(recipe, prices)
    if not math.isfinite(variable) or variable <= 0.0 or revenue < variable:
        return 1.0
    return producers.share_working(revenue, variable)
