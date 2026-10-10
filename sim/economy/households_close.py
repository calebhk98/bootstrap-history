"""A cohort's year end: what it used up, what it went short of, and what it now expects.

Non-durables received are consumed (moved to the consumption edge); durables stay with the cohort in
the book and serve at a yearly rate of one over their service life. The floor of each need is compared
with what the cohort got of it; the shortfall is recorded for demography to read as hunger.
"""
from typing import Dict, List, Mapping, Tuple

from . import currency, durable_stock
from .households_basket import Basket, need_prices, subsistence_cost_per_person
from .households_cohort import Cohort, renewed
from .households_own import next_own_plan
from .protocols import MarketView
from .types import EDGE_CONSUMPTION, GoodId, GoodsMove, GoodSpec


def _is_durable(good: GoodId, specs: Mapping[GoodId, GoodSpec]) -> bool:
    spec = specs.get(good)
    return spec is not None and spec.service_life_years > 0.0


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


def close_year(cohort: Cohort, received_by_good: Mapping[GoodId, float], view: MarketView,
               specs: Mapping[GoodId, GoodSpec], basket: Basket, income_received: float = 0.0,
               spent: float = 0.0) -> Tuple[Cohort, List[GoodsMove]]:
    """The cohort after the year and the consumption moves to book. `income_received` and `spent` are
    the year's money flows, which the caller reads from the book."""
    moves = [GoodsMove(cohort.agent_id, EDGE_CONSUMPTION, good, cohort.tile, quantity, "consumption")
             for good, quantity in sorted(received_by_good.items())
             if quantity > 0.0 and not _is_durable(good, specs)]
    unmet = unmet_floor_by_need(cohort, received_by_good, view, specs, basket)
    first_good = next((need.goods[0][0] for need in basket.needs if need.goods), None)
    floor_cost = subsistence_cost_per_person(need_prices(basket, view, cohort.tile)) * cohort.people
    expected, level, target = cohort.expected_inflation, cohort.last_basket_price_level, cohort.cash_target
    if first_good is not None:
        money = view.currency_of(view.area_of(first_good, cohort.tile))
        level = view.basket_price_level(money)
        expected = currency.update_expected_inflation(
            cohort.expected_inflation, level / cohort.last_basket_price_level - 1.0)
        target = currency.cash_balance_target(spent or income_received, view.interest_rate(money), expected)
    return renewed(cohort, expected_inflation=expected, last_basket_price_level=level, cash_target=target,
                   last_year_income=income_received, last_year_spending=spent,
                   expected_spending=durable_stock.update_expected_spending(cohort.expected_spending, spent),
                   expected_floor_cost=durable_stock.update_expected_spending(cohort.expected_floor_cost, floor_cost),
                   unmet_floor_by_need=unmet,
                   own_plan_by_need=next_own_plan(cohort.own_plan_by_need, unmet, spent < income_received)), moves
