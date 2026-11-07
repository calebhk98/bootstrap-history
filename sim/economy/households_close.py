"""A cohort's year end: what it used up, what it went short of, and what it now expects.

Non-durables received are consumed (moved to the consumption edge); durables stay with the cohort in
the book and serve at a yearly rate of one over their service life. The floor of each need is compared
with what the cohort got of it; the shortfall is recorded for demography to read as hunger.
"""
from typing import Dict, List, Mapping, Optional, Tuple

from . import currency, durable_stock, households_buffer_stock, opening_resting
from sim.world import need_basket
from sim.world.need_basket import Basket, subsistence_cost_per_person
from .households_cohort import Cohort, renewed
from .households_own import next_own_plan
from .protocols import MarketView
from .types import EDGE_CONSUMPTION, GoodId, GoodsMove, GoodSpec


def _is_durable(good: GoodId, specs: Mapping[GoodId, GoodSpec]) -> bool:
    spec = specs.get(good)
    return spec is not None and spec.service_life_years > 0.0


def _priced_needs(basket: Basket, view: MarketView, tile: str, offered_prices: Dict[Tuple[GoodId, str], float]):
    """`households_basket.need_prices` with each good's offered price read once per tile into `offered_prices`."""
    def price_of(good: GoodId):
        if (good, tile) not in offered_prices:
            offered_prices[(good, tile)] = view.offered_price(good, view.area_of(good, tile))
        return offered_prices[(good, tile)]
    return list(need_basket.need_prices(basket, price_of))


def unmet_floor_by_need(cohort: Cohort, received_by_good: Mapping[GoodId, float], view: MarketView,
                        specs: Mapping[GoodId, GoodSpec], basket: Basket) -> Dict[str, float]:
    unmet = {}
    for need in basket.needs:
        floor_units = need.subsistence_per_person * cohort.people
        if floor_units <= 0.0:
            continue
        delivered = 0.0
        for good, effect in need.goods:
            if _is_durable(good, specs):
                held = view.stock(cohort.agent_id, good, cohort.tile)
                delivered += held * effect / specs[good].service_life_years
            else:
                delivered += received_by_good.get(good, 0.0) * effect
        if delivered < floor_units:
            unmet[need.need_id] = floor_units - delivered
    return unmet


def floor_cost_per_person(basket: Basket, view: MarketView, tile: str,
                          offered_prices: Optional[Dict[Tuple[GoodId, str], float]] = None) -> float:
    """What one person's floors cost a year on the tile at the prices offered there."""
    return subsistence_cost_per_person(_priced_needs(basket, view, tile, {} if offered_prices is None else offered_prices))


def close_year(cohort: Cohort, received_by_good: Mapping[GoodId, float], view: MarketView,
               specs: Mapping[GoodId, GoodSpec], basket: Basket, income_received: float = 0.0,
               spent: float = 0.0, offered_prices: Optional[Dict[Tuple[GoodId, str], float]] = None,
               floor_cost_of_person: Optional[float] = None) -> Tuple[Cohort, List[GoodsMove]]:
    """The cohort after the year and the consumption moves to book. `income_received` and `spent` are
    the year's money flows, which the caller reads from the book. `offered_prices` (good, tile) -> offered price
    is filled as cohorts are closed, so a pass over many cohorts reads each price once. `floor_cost_of_person` is
    `floor_cost_per_person` for the cohort's basket and tile when the caller has it already (cohorts of one basket share it)."""
    moves = [GoodsMove(cohort.agent_id, EDGE_CONSUMPTION, good, cohort.tile, quantity, "consumption")
             for good, quantity in sorted(received_by_good.items())
             if quantity > 0.0 and not _is_durable(good, specs)]
    unmet = unmet_floor_by_need(cohort, received_by_good, view, specs, basket)
    first_good = next((need.goods[0][0] for need in basket.needs if need.goods), None)
    if floor_cost_of_person is None:
        floor_cost_of_person = floor_cost_per_person(basket, view, cohort.tile, offered_prices)
    floor_cost = floor_cost_of_person * cohort.people
    expected, level, target = cohort.expected_inflation, cohort.last_basket_price_level, cohort.cash_target
    share_wealth = cohort.share_wealth
    if first_good is not None:
        money = view.currency_of(view.area_of(first_good, cohort.tile))
        level = view.basket_price_level(money)
        observed = view.observed_inflation(money)
        if observed is None:
            observed = level / cohort.last_basket_price_level - 1.0
        expected = currency.update_expected_inflation(cohort.expected_inflation, observed)
        # the cash the spending rule rests at: the one figure for cash wanted (mint, lending and the opening read it)
        share_wealth = view.equity(cohort.agent_id)
        target = opening_resting.resting_household_purse(
            households_buffer_stock.mean_net_income(income_received, cohort.last_year_income),
            share_wealth, view.claims(cohort.agent_id, money))
    return renewed(cohort, expected_inflation=expected, last_basket_price_level=level, cash_target=target,
                   share_wealth=share_wealth, last_year_income=income_received,
                   expected_spending=durable_stock.update_expected_spending(cohort.expected_spending, spent, cohort.planned_spending),
                   planned_spending=0.0,
                   expected_floor_cost=durable_stock.update_expected_spending(cohort.expected_floor_cost, floor_cost),
                   unmet_floor_by_need=unmet,
                   own_plan_by_need=next_own_plan(cohort.own_plan_by_need, unmet, spent < income_received)), moves
