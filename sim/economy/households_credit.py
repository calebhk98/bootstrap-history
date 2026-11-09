"""A household borrows to cover a subsistence shortfall when it has income ahead (consumption smoothing).

`subsistence_request` asks for the floor cost its cash does not cover, no more than its expected income can
service; what it will pay is what that income allows. The credit market rations it through
the risk premium on a borrower with no collateral. `floor_bids` spends a loan on the floors it was for.
"""
import math
from typing import List, Mapping, Optional

from sim.constants import declare

from . import credit
from sim.world.need_basket import Basket
from .households_cohort import Cohort
from .households_orders import FLOOR_BUDGET_PRICE_MARGIN
from .priced_need_list import priced_needs_of
from sim.book import ROUNDING_SHARE
from .types import Bid, CurrencyId, GoodId, GoodSpec, LoanRequest

HOUSEHOLD_LOAN_YEARS = declare(
    "HOUSEHOLD_LOAN_YEARS", 2.0, kind="temporary_heuristic", unit="years",
    source=None, confidence="D",
    why="A subsistence loan is repaid over a couple of harvests. Real terms follow the lender and the "
        "borrower's income cycle, which are not modelled.")
HOUSEHOLD_SERVICE_SHARE = declare(
    "HOUSEHOLD_SERVICE_SHARE", 0.25, kind="temporary_heuristic", unit="share of expected yearly income",
    source=None, confidence="D",
    why="The most of its income a household commits to debt service before it would rather go short. "
        "Stands in for what lenders will accept and what a family can bear, which are not modelled.")


def floor_cost_unmet(cohort: Cohort, priced, grown_units: Optional[Mapping[str, float]]) -> float:
    """What the cohort's subsistence floors cost at last year's prices, less what its own plot grew."""
    grown_units = grown_units or {}
    return math.fsum(price_index * max(0.0, spec.subsistence_per_person * cohort.people - grown_units.get(spec.need_id, 0.0))
                     for spec, price_index, _first, _end in priced_needs_of(priced).blocks())


def subsistence_request(cohort: Cohort, shortfall: float, currency: CurrencyId, live_rate: float,
                        existing_debt: float) -> Optional[LoanRequest]:
    """A loan for `shortfall`, bounded so that its service and the debt already owed stay within the
    declared share of the income the household expects (last year's). None when it has no income ahead."""
    capacity = HOUSEHOLD_SERVICE_SHARE * cohort.last_year_income - existing_debt * (
        max(0.0, live_rate) + 1.0 / HOUSEHOLD_LOAN_YEARS)
    if shortfall <= ROUNDING_SHARE * cohort.last_year_income or capacity <= 0.0:
        return None
    per_unit_service = 1.0 / HOUSEHOLD_LOAN_YEARS + max(0.0, live_rate)
    amount = min(shortfall, capacity / per_unit_service)
    affordable_rate = (capacity - amount / HOUSEHOLD_LOAN_YEARS) / amount
    return LoanRequest(cohort.agent_id, currency, amount, credit.earnable_rate(affordable_rate),
                       HOUSEHOLD_LOAN_YEARS, 0.0, "subsistence")


def floor_bids(cohort: Cohort, priced, budget: float, grown_units: Optional[Mapping[str, float]],
               specs: Mapping[GoodId, GoodSpec], view, basket: Basket) -> List[Bid]:
    """Bids for the floors of the needs, budget spread over them by cost, for goods used up in the year
    (a durable is bought as replacement by the household's own orders)."""
    grown_units = grown_units or {}
    wanted = []
    priced = priced_needs_of(priced)
    names, prices, shares = priced.columns.names, priced.columns.price, priced.columns.share
    for need_spec, price_index, first, end in priced.blocks():
        units = max(0.0, need_spec.subsistence_per_person * cohort.people - grown_units.get(need_spec.need_id, 0.0))
        for row in range(first, end):
            good, price = names[row], prices[row]
            spec = specs.get(good)
            if units > 0.0 and (spec is None or spec.service_life_years <= 0.0):
                wanted.append((good, price, units * price_index * shares[row] / price))
    total = math.fsum(quantity * price for _good, price, quantity in wanted)
    if total <= 0.0 or budget <= 0.0:
        return []
    scale = min(1.0, budget / total)
    return [Bid(cohort.agent_id, good, view.area_of(good, cohort.tile), cohort.tile, quantity, 0.0, price,
                basket.substitution, quantity * price * scale, 0,
                maximum_price=price * (1.0 + FLOOR_BUDGET_PRICE_MARGIN)) for good, price, quantity in wanted]
