"""A cohort's goods bids for the year, planned on last year's prices.

Spending this year is income plus the adjustment that brings cash back to its target. The floors of
the needs (subsistence) are served first; what is left over is surplus spending, split across the needs
by their budget weights (Stone-Geary: a floor plus a marginal share of the surplus). Inside a need the
spending goes to goods by cost per need unit. A need with a per-head limit stops taking money at it.
A durable is demanded as replacement: the stock that serves the need's flow over the good's life, less
what is held after this year's wear.

The sum of every bid's budget never exceeds cash: floors are budgeted first (with room for a price
rise), surplus spending only from what remains.
"""
import math
from typing import Dict, List, Mapping, Optional

from sim.constants import declare

from . import currency, durable_stock
from .credit_view import claims_of
from .households_ability import affordable_goods, household_budget_for_need
from .households_basket import Basket, PricedNeed, need_prices, need_units, price_ceilings
from .households_cohort import Cohort
from .protocols import AgentOrders, MarketView
from .types import Bid, FundsOffer, GoodId, GoodSpec

FLOOR_BUDGET_PRICE_MARGIN = declare(
    "FLOOR_BUDGET_PRICE_MARGIN", 0.25, kind="temporary_heuristic",
    unit="share of the floor's cost at last year's prices", source=None, confidence="D",
    why="A household sets aside more than last year's price for its subsistence goods, in case prices "
        "rose before it buys. Above that rise it goes short. Real households keep reserves and shop "
        "around, which are not modelled.")
BUDGET_SAFETY_SHARE = 1e-9

HOUSEHOLD_TIME_PREFERENCE = declare(
    "HOUSEHOLD_TIME_PREFERENCE", 0.05, kind="temporary_heuristic",
    unit="share a year", source=None, confidence="D",
    why="A household lends its savings only for at least what it gives up by waiting, on top of what "
        "inflation it expects takes from them. The figure is a common assumption in growth models, "
        "not measured for any society here; default risk is priced separately by the credit market.")
SAVINGS_YEARS_OF_SURPLUS_INCOME = declare(
    "SAVINGS_YEARS_OF_SURPLUS_INCOME", 2.0, kind="temporary_heuristic",
    unit="years of income above subsistence kept as savings when the real rate equals time preference",
    source=None, confidence="D",
    why="Households beyond subsistence keep savings against dearth, dowries, old age and burial, and lend "
        "what they do not hold as cash. How many years of surplus income they kept is not measured for any "
        "society here; probate inventories and dowry records would bound it.")
SAVINGS_RATE_RESPONSE_LIMIT = declare(
    "SAVINGS_RATE_RESPONSE_LIMIT", 2.0, kind="temporary_heuristic",
    unit="largest multiple of the savings target a high real rate draws", source=None, confidence="D",
    why="Saving rises with what it earns but not without bound; the bound stands in for the income effect "
        "that a model of lifetime choice would give.")
SAVINGS_RESPONSE_FLOOR = declare(
    "SAVINGS_RESPONSE_FLOOR", 1.0, kind="temporary_heuristic",
    unit="share of the savings target kept when cash earns nothing in real terms", source=None,
    confidence="D",
    why="Households do not stop saving because expected inflation reaches the interest rate: they hold the "
        "wealth in other forms (the durable store takes more of it then) and smooth. The floor stands in "
        "for that portfolio choice and for the saving motives that do not depend on the return (dearth, "
        "dowry, old age); no society's saving is measured against the real rate here.")
WEALTH_DRAWDOWN_LIMIT = declare(
    "WEALTH_DRAWDOWN_LIMIT", 1.0, kind="temporary_heuristic",
    unit="share of a year's income that wealth above target may add to spending in a year", source=None,
    confidence="D",
    why="Households smooth consumption: wealth above what they want to keep is spent down over several "
        "years, not in the one year their target falls. Without a limit a fall in the target sends the "
        "whole stock of cash to the shops at once and nothing is left to lend. The pace is an assumption; "
        "no society's spending is measured against its wealth here.")

SPENDING_CUT_LIMIT = declare(
    "SPENDING_CUT_LIMIT", 0.3, kind="temporary_heuristic",
    unit="largest share of its expected spending a household cuts in a year", source=None, confidence="D",
    why="Households smooth consumption: a rise in the wealth they want to hold is saved over several years, "
        "not in the one year it appears. The share is an assumption; no society's spending is measured "
        "against its expected spending here.")


def savings_target(surplus_income: float, interest_rate: float, expected_inflation: float) -> float:
    """Wealth a household wants to keep beyond its cash buffer: years of its income above subsistence,
    more when saving pays more in real terms (bounded, and never below a floor, since wealth held as goods
    counts toward it); none at subsistence."""
    if surplus_income <= 0.0:
        return 0.0
    real_rate = max(0.0, interest_rate - expected_inflation)
    response = max(SAVINGS_RESPONSE_FLOOR,
                   min(SAVINGS_RATE_RESPONSE_LIMIT, real_rate / HOUSEHOLD_TIME_PREFERENCE))
    return SAVINGS_YEARS_OF_SURPLUS_INCOME * surplus_income * response


def _durable_ratio(good: GoodId, flow: float, held: float, specs: Mapping[GoodId, GoodSpec],
                   scale: float = 1.0) -> float:
    """1.0 for a good used up in the year; for a durable, replacement over the flow it serves. The stock
    wanted is sized on the expected flow (`scale` times this year's)."""
    spec = specs.get(good)
    if spec is None or spec.service_life_years <= 0.0:
        return 1.0
    if flow <= 0.0:
        return 0.0
    wear = held * min(1.0, 1.0 / spec.service_life_years)
    return max(0.0, flow * scale * spec.service_life_years - held + wear) / flow


def _smoothed_flow_by_good(cohort: Cohort, priced: List[PricedNeed], basket: Basket
                           ) -> Dict[GoodId, float]:
    """The yearly flow of each good the smoothed surplus (smoothed spending over smoothed floor cost) buys,
    with the goods the cohort could afford on it: it sizes the stock of a durable that a bad year, in which
    the floors take nearly all spending or a good is unaffordable, would otherwise size at nothing."""
    if cohort.expected_spending <= 0.0 or cohort.expected_floor_cost <= 0.0:
        return {}
    stock_floors, stock_totals = need_units(priced, basket, cohort.people,
                                            cohort.expected_spending - cohort.expected_floor_cost)
    flows: Dict[GoodId, float] = {}
    for need in priced:
        need_id = need.spec.need_id
        affordable, affordable_share, household_cap = affordable_goods(
            need.goods, household_budget_for_need(stock_totals[need_id], need.price_index, cohort.people),
            need.spec.subsistence_per_person > 0.0)
        for good, price, effect, share in need.goods:
            if affordable[good]:
                per_unit = need.price_index * share / price / affordable_share
                flows[good] = flows.get(good, 0.0) + (stock_floors[need_id] + max(
                    0.0, stock_totals[need_id] - stock_floors[need_id])) * per_unit
    return flows


def goods_orders(cohort: Cohort, view: MarketView, cash: float, income_this_year: float,
                 basket: Basket, specs: Mapping[GoodId, GoodSpec],
                 priced: Optional[List[PricedNeed]] = None, smooth_rise: bool = True) -> AgentOrders:
    """`priced` may be passed (from `need_prices`) to share the price work among a tile's classes.
    `smooth_rise` False lifts the bound on a rise in spending: an economy finding its level from an opening
    that holds more money than its households want to keep would otherwise approach it over years."""
    priced = need_prices(basket, view, cohort.tile) if priced is None else priced
    cash = max(0.0, cash)
    if not priced or cohort.people <= 0.0:
        return AgentOrders()
    first_good = priced[0].goods[0][0]
    area_currency = view.currency_of(view.area_of(first_good, cohort.tile))
    reference_spending = cohort.last_year_spending or income_this_year
    target = cohort.cash_target or currency.cash_balance_target(
        reference_spending, view.interest_rate(area_currency), cohort.expected_inflation)
    floor_cost = math.fsum(need.price_index * need.spec.subsistence_per_person * cohort.people
                           for need in priced)
    # what it has lent counts toward the wealth it spends from, so a loss to default cuts its spending;
    # it spends down only wealth above its cash buffer and the savings it wants to keep
    claims = claims_of(view, cohort.agent_id, area_currency)
    from . import households_store            # imported here: that module needs this one's constants
    weights, store_prices, held = households_store.store_holding(cohort, view, specs, priced)
    store_value = math.fsum(held[good] * store_prices[good] for good in weights)
    keep = target + savings_target(income_this_year - floor_cost, view.interest_rate(area_currency),
                                   cohort.expected_inflation)
    # the pace is set by the larger of this year's and last year's income, since a year's income so far
    # understates a household's usual income in its first year
    drawdown = min(currency.spending_adjustment(cash + claims + store_value, keep, income_this_year),
                   WEALTH_DRAWDOWN_LIMIT * max(0.0, income_this_year, cohort.last_year_income))
    spending = max(0.0, min(cash, income_this_year + drawdown))
    if cohort.expected_spending > 0.0:
        # a rise in the savings target is saved over years, not at once; a windfall is spent over years too
        if smooth_rise:
            spending = min(spending, max(income_this_year, (1.0 + SPENDING_CUT_LIMIT) * cohort.expected_spending))
        spending = max(spending, min(cash, (1.0 - SPENDING_CUT_LIMIT) * cohort.expected_spending))
    floors, totals = need_units(priced, basket, cohort.people, spending - floor_cost)
    # the stock of a durable is sized on the expected flow: this year's flow scaled by expected over actual
    # spending, but never below the flow the smoothed surplus (smoothed spending over smoothed floor cost)
    # buys, since the scaled flow vanishes when the floors take nearly all of a bad year's spending
    scale = durable_stock.expected_flow_scale(cohort.expected_spending, spending)
    smoothed_flow = _smoothed_flow_by_good(cohort, priced, basket)
    rows = []
    flow_by_good = {}
    for need in priced:
        need_id = need.spec.need_id
        ceilings = need.ceilings or price_ceilings(need.goods)
        affordable, affordable_share, household_cap = affordable_goods(
            need.goods, household_budget_for_need(totals[need_id], need.price_index, cohort.people),
            need.spec.subsistence_per_person > 0.0)
        for (good, price, effect, share), ceiling in zip(need.goods, ceilings):
            if not affordable[good]:
                continue
            ceiling = min(ceiling, household_cap)
            per_unit = need.price_index * share / price / affordable_share
            floor_quantity = floors[need_id] * per_unit
            flexible_quantity = max(0.0, totals[need_id] - floors[need_id]) * per_unit
            flow = floor_quantity + flexible_quantity
            flow_by_good[good] = flow_by_good.get(good, 0.0) + flow
            stock_flow = max(flow * scale, smoothed_flow.get(good, 0.0))
            ratio = _durable_ratio(good, flow, view.stock(cohort.agent_id, good, cohort.tile), specs,
                                   stock_flow / flow if flow > 0.0 else 1.0)
            if ratio > 0.0 and floor_quantity + flexible_quantity > 0.0:
                rows.append((need.spec.subsistence_per_person > 0.0, good, price,
                             floor_quantity * ratio, flexible_quantity * ratio, ceiling))
    floor_spend = math.fsum(row[2] * row[3] for row in rows)
    flexible_spend = math.fsum(row[2] * row[4] for row in rows)
    floor_wanted = floor_spend * (1.0 + FLOOR_BUDGET_PRICE_MARGIN)
    usable = cash * (1.0 - BUDGET_SAFETY_SHARE)
    floor_scale = min(1.0, usable / floor_wanted) if floor_wanted > 0.0 else 0.0
    # surplus goes on only what the year's spending allows, so stocking up a durable is paid from income
    left = min(usable, max(spending, floor_wanted * floor_scale)) - floor_wanted * floor_scale
    flexible_scale = min(1.0, left / flexible_spend) if flexible_spend > 0.0 else 0.0
    bids = []
    budget_total = 0.0
    for has_floor, good, price, floor, flex, ceiling in sorted(rows, key=lambda row: row[1]):
        budget = (floor * price * (1.0 + FLOOR_BUDGET_PRICE_MARGIN) * floor_scale
                  + flex * price * flexible_scale)
        if budget <= 0.0:
            continue
        budget_total += budget
        bids.append(Bid(cohort.agent_id, good, view.area_of(good, cohort.tile), cohort.tile,
                        floor, flex, price, basket.substitution, budget, 0 if has_floor else 1,
                        maximum_price=ceiling))
    funds = ()
    savings = cash - budget_total - target
    offers = ()
    if weights:
        # stock kept in use serves the needs and is not savings, so the store sees only the rest
        stock_flow_by_good = {good: max(flow_by_good.get(good, 0.0) * scale, smoothed_flow.get(good, 0.0))
                              for good in set(flow_by_good) | set(smoothed_flow)}
        in_use = durable_stock.in_use_stock(stock_flow_by_good, specs, 1.0, households_store.STORE_REBALANCE_BAND)
        held = {good: max(0.0, quantity - in_use.get(good, 0.0)) for good, quantity in held.items()}
        real_rate = view.interest_rate(area_currency) - cohort.expected_inflation
        above_buffer = cash + claims + store_value - target
        store_bids, store_spend = households_store.store_bids(
            cohort, view, specs, basket, weights, store_prices, held, above_buffer, real_rate,
            min(savings, usable - budget_total))
        bids.extend(store_bids)
        savings -= store_spend
        offers = tuple(households_store.store_offers(cohort, view, specs, weights, store_prices, held,
                                                     above_buffer, real_rate, cash, floor_cost))
    if savings > 0.0:
        funds = (FundsOffer(cohort.agent_id, area_currency, savings,
                            max(0.0, HOUSEHOLD_TIME_PREFERENCE + cohort.expected_inflation)),)
    return AgentOrders(bids=tuple(bids), offers=offers, funds_offers=funds)
