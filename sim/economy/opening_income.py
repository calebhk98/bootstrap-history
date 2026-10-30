"""The opening's household income, settled with the demand it pays for.

An opening that gives every worker a full year of work at the opening wage pays out far more than the
households spend (their needs are met well short of it) and far more than the producers sized to what they
spend can pay: the first year's realised income is a fraction of the opening figure and the wage falls to
meet the hours nobody hires. Here income is the value of what the opening makes. At prices that equal costs
the factor payments (wages, rent, the plant's charge) add up to the value of final demand, so the income the
households receive is the income that pays for the demand producers are sized to.

The rule: the opening's income per head is the largest income, up to the full-employment ceiling, at which
households save nothing net. Households spend all of a low income (less the margin their bids leave unspent),
and above some income they begin to keep a surplus (spending is mean income plus a share of the account held, see
households_buffer_stock). Nothing
in the final demand spends that saving (no plant, working capital or lending demand is counted), so demand falls
short of income from there up; income then has no fixed point above that kink and every income below it is one
(demand equals income). A stationary economy saves nothing net: its saving is matched by demand that does not
come from its own income (replacement, investment, the state's spending, exports), and the demand counted here
carries only the metal the money loses (an autonomous part). Where more of that demand is counted (Complaint 607),
the income at which households stop saving rises with it, with no change here. The income is found by a root
find on the income left unspent, not by iterating income into demand: that map has propensity almost one with no
intercept, so it falls a little a pass without reaching a fixed point and stops wherever its pass bound does.
"""
import math
from typing import Callable, Dict, Mapping, Tuple, Union

from sim.refusal import Refusal

from .households_cohort import Cohort
from .households_orders import BUDGET_SAFETY_SHARE
from .types import GoodId, TileId

# the share of its income a household may leave unspent and still count as saving nothing: above the margin its bids
# leave unspent by construction (BUDGET_SAFETY_SHARE), below any saving that moves a price
SAVING_TOLERANCE = 5e-8
OPENING_INCOME_TOLERANCE = 1e-6     # relative width of the bracket the income is found in
# numerical bounds, not behaviour: the halvings that look for an income at which households save nothing (below the
# ceiling by a factor no income is bought at) and the passes of the root find, which converges in a handful
OPENING_INCOME_HALVINGS = 30
OPENING_INCOME_PASSES = 100


def value_of(final_by_tile: Mapping[TileId, Mapping[GoodId, float]], prices: Mapping[GoodId, float]) -> float:
    """Money value of a final demand at the prices given."""
    return math.fsum(quantity * prices.get(good, 0.0)
                     for demand in final_by_tile.values() for good, quantity in demand.items())


def settled_income_per_head(ceiling: float, people: float, demand_at: Callable[[float], Tuple[float, float]]
                            ) -> Union[Tuple[float, float], Refusal]:
    """(income per head, labour share of it) at which households save nothing net: the `ceiling` (full employment at
    the opening wage) when they spend all of it, else the largest income below it at which the value of the demand
    that income buys, per head, covers the income (up to SAVING_TOLERANCE of it). `demand_at(income per head)` gives
    the value of the demand that income buys and the share of that value which pays labour. A Refusal when there are
    no people, or no positive income at which households save nothing (`no_positive_income_fixed_point`), or the root
    find does not close (`income_root_not_found`)."""
    if people <= 0.0 or ceiling <= 0.0:
        return Refusal("no_people_to_pay", "The opening has no people to pay an income to.", people=people, ceiling=ceiling)
    seen: Dict[float, float] = {}

    def unspent(income):
        """Income left unspent past the tolerance (at most zero where households save nothing net)."""
        value, labour_share = demand_at(income)
        seen[income] = labour_share
        return income - value / people - SAVING_TOLERANCE * income

    unspent_high = unspent(ceiling)
    if unspent_high <= 0.0:
        return ceiling, seen[ceiling]
    # Above the kink the unspent income is smooth and rises, so a line through the two lowest incomes that still
    # save finds where it crosses zero; an income that saves nothing brackets the root, and where the line leaves
    # the bracket (or there is only one such income) the bracket is halved.
    high, previous_high, previous_unspent = ceiling, None, 0.0
    low = None
    looked_past_low = False
    for _pass in range(OPENING_INCOME_PASSES):
        floor = 0.0 if low is None else low
        income = None
        if previous_high is not None and unspent_high != previous_unspent:
            income = high - unspent_high * (high - previous_high) / (unspent_high - previous_unspent)
        if low is not None and not looked_past_low and (income is None or income <= floor):
            looked_past_low = True      # the line puts the root at the bracket's low end: look just past it, once
            income = floor * (1.0 + OPENING_INCOME_TOLERANCE)
        if income is None or not floor < income < high:
            income = (floor + high) / 2.0
            if low is None and income < ceiling * 0.5 ** OPENING_INCOME_HALVINGS:
                return Refusal("no_positive_income_fixed_point",
                               "At no income does the demand it buys cover the income: households save at every level.",
                               ceiling=ceiling, lowest_income_tried=high, halvings=OPENING_INCOME_HALVINGS)
        unspent_income = unspent(income)
        if unspent_income <= 0.0:
            low = income
            if high - low <= OPENING_INCOME_TOLERANCE * high:
                return low, seen[low]
        else:
            if low is not None and income - low <= OPENING_INCOME_TOLERANCE * income:
                return low, seen[low]
            converged = high - income <= OPENING_INCOME_TOLERANCE * income
            previous_high, previous_unspent, high, unspent_high = high, unspent_high, income, unspent_income
            if converged:
                return high, seen[high]
    return Refusal("income_root_not_found", "The income at which households stop saving was not found within the passes allowed.",
                   ceiling=ceiling, low=low, high=high, passes=OPENING_INCOME_PASSES)


def producible_share(runs: Mapping[str, float], recipes: Mapping[str, object], hands_hours: float) -> float:
    """The share of the demand the producers of `runs` could make with the hours the working people have
    (`hands_hours`, a year): one when the runs' labour hours fit, else hands over hours needed. An income that
    asks for more than the hands can make is not an income the producers can pay out."""
    needed = math.fsum(count * math.fsum(recipes[recipe_id].labour_hours.values()) for recipe_id, count in runs.items())
    return 1.0 if needed <= hands_hours or needed <= 0.0 else max(0.0, hands_hours) / needed


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
