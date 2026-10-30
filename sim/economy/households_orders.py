"""A cohort's goods bids for the year, planned on last year's prices.

Spending this year is income plus the adjustment that brings cash back to its target. The floors of
the needs (subsistence) are served first; what is left over is surplus spending, split across the needs
by their budget weights (Stone-Geary: a floor plus a marginal share of the surplus). Inside a need the
spending goes to goods by cost per need unit. A need with a per-head limit stops taking money at it.
A durable is demanded as replacement: the stock that serves the need's flow over the good's life, less
what is held after the previous year's wear.

The sum of every bid's budget never exceeds cash: floors are budgeted first (with room for a price
rise), surplus spending only from what remains.
"""
import math
from typing import Dict, List, Mapping, Optional

from sim.constants import declare

from . import currency, durable_stock, households_buffer_stock
from . import lender_ask
from .credit_view import claims_of, equity_of, loss_rate_of
from .households_ability import affordable_goods, household_budget_for_need
from .households_basket import (Basket, PricedNeed, need_prices, need_units, price_ceilings, quality_reach,
                                with_quality_reach)
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
    unit="share a year", source=(
        'No source found: a discount rate read from a source that could be opened was not found. Not '
        'measured for any pre-modern society.'), confidence="D",
    why="A household lends its savings only for at least what it gives up by waiting, on top of what "
        "inflation it expects takes from them. The figure is a common assumption in growth models, "
        "not measured for any society here; default risk is priced separately by the credit market.",
    retire="Complaints/607: the opening holds the wealth its households want and saving has a user")
WEALTH_DRAWDOWN_LIMIT = declare(
    "WEALTH_DRAWDOWN_LIMIT", 1.0, kind="temporary_heuristic",
    unit="share of a year's income that wealth above target may add to spending in a year", source=(
        'No source found: the pace at which a household spends wealth above target was not found in '
        'a source that could be opened. The pace is an assumption.'),
    confidence="D",
    why="Households smooth consumption: wealth above what they want to keep is spent down over several "
        "years, not in the one year their target falls. Without a limit a fall in the target sends the "
        "whole stock of cash to the shops at once and nothing is left to lend. The pace is an assumption; "
        "no society's spending is measured against its wealth here.",
    retire="Complaints/607: the opening holds the wealth its households want and saving has a user")

SPENDING_CUT_LIMIT = declare(
    "SPENDING_CUT_LIMIT", 0.3, kind="temporary_heuristic",
    unit="largest share of its expected spending a household cuts in a year", source=(
        'No source found: the share of expected spending a household cuts in a year was not found in '
        'a source that could be opened. The share is an assumption.'), confidence="D",
    why="Households smooth consumption: a rise in the wealth they want to hold is saved over several years, "
        "not in the one year it appears. The share is an assumption; no society's spending is measured "
        "against its expected spending here.",
    retire="Complaints/607: the opening holds the wealth its households want and saving has a user")


def _durable_ratio(good: GoodId, flow: float, held: float, specs: Mapping[GoodId, GoodSpec],
                   scale: float = 1.0) -> float:
    """1.0 for a good used up in the year; for a durable, replacement over the flow it serves. The stock
    wanted is sized on the expected flow (`scale` times this year's)."""
    spec = specs.get(good)
    if spec is None or spec.service_life_years <= 0.0:
        return 1.0
    if flow <= 0.0:
        return 0.0
    return max(0.0, flow * scale * spec.service_life_years - held) / flow


def _smoothed_flow_by_good(cohort: Cohort, priced: List[PricedNeed], basket: Basket,
                           spending: Optional[float] = None, floor_cost: Optional[float] = None
                           ) -> Dict[GoodId, float]:
    """The yearly flow of each good the smoothed surplus (smoothed spending over smoothed floor cost) buys,
    with the goods the cohort could afford on it: it sizes the stock of a durable that a bad year, in which
    the floors take nearly all spending or a good is unaffordable, would otherwise size at nothing."""
    spending = cohort.expected_spending if spending is None else spending
    floor_cost = cohort.expected_floor_cost if floor_cost is None else floor_cost
    if spending <= 0.0 or floor_cost <= 0.0:
        return {}
    stock_floors, stock_totals = need_units(priced, basket, cohort.people, spending - floor_cost)
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


def _store_value_outside_use(cohort: Cohort, priced: List[PricedNeed], basket: Basket, specs: Mapping[GoodId, GoodSpec],
                             weights, prices, held, cash: float, owned: float,
                             income: float, floor_cost: float, last_year_income: float = 0.0) -> float:
    """What the cohort holds of the store goods that is wealth to spend from. A durable kept in use serves a
    need and is not wealth, so what the flow of its needs keeps in use is left out; the flow is read at the
    spending the other wealth allows, so that stocking a durable does not itself move the household to
    other goods."""
    from . import households_store            # imported here: that module needs this one's constants
    in_use_goods = [good for good in weights if held[good] > 0.0 and specs[good].service_life_years > 0.0]
    value = math.fsum(held[good] * prices[good] for good in weights if good not in in_use_goods)
    if not in_use_goods:
        return value
    provisional = households_buffer_stock.spending_budget(households_buffer_stock.mean_net_income(income, last_year_income), cash, owned)
    reached = with_quality_reach(priced, basket, quality_reach(provisional, floor_cost))
    in_use = durable_stock.in_use_stock(_smoothed_flow_by_good(cohort, reached, basket, provisional, floor_cost),
                                        specs, 1.0, households_store.STORE_REBALANCE_BAND)
    return value + math.fsum(max(0.0, held[good] - in_use.get(good, 0.0)) * prices[good] for good in in_use_goods)


def goods_orders(cohort: Cohort, view: MarketView, cash: float, income_this_year: float,
                 basket: Basket, specs: Mapping[GoodId, GoodSpec],
                 priced: Optional[List[PricedNeed]] = None, smooth_rise: bool = True,
                 shared_store: Optional[dict] = None, stationary_durables: bool = False) -> AgentOrders:
    """`priced` may be passed (from `need_prices`) to share the price work among a tile's classes.
    `smooth_rise` False lifts the bound on a rise in spending: an economy finding its level from an opening
    that holds more money than its households want to keep would otherwise approach it over years.
    `shared_store` (empty to begin with) lets the cohorts of one pass share each tile's store prices.
    `stationary_durables` sizes opening demand at replacement of the solved stock, before that stock is seeded."""
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
    # spending follows Eurace's consumption budget (households_buffer_stock): mean net income, cash, shares
    claims = claims_of(view, cohort.agent_id, area_currency)
    from . import households_store            # imported here: that module needs this one's constants
    weights, store_prices, held = households_store.store_holding(cohort, view, specs, priced, shared_store)
    # the pace is set by the larger of this year's and last year's income, since a year's income so far
    # understates a household's usual income in its first year
    owned = equity_of(view, cohort.agent_id)     # what it owns of the firms is wealth it already holds
    store_value = _store_value_outside_use(cohort, priced, basket, specs, weights, store_prices, held,
                                           cash, owned, income_this_year, floor_cost, cohort.last_year_income)
    mean_income = households_buffer_stock.mean_net_income(income_this_year, cohort.last_year_income)
    budget = households_buffer_stock.spending_budget(mean_income, cash, owned, claims)
    drawdown = min(budget - income_this_year,
                   WEALTH_DRAWDOWN_LIMIT * max(0.0, income_this_year, cohort.last_year_income))
    spending = max(0.0, min(cash, income_this_year + drawdown))
    if cohort.expected_spending > 0.0:
        # a rise in the savings target is saved over years, not at once; a windfall is spent over years too
        if smooth_rise:
            spending = min(spending, max(income_this_year, (1.0 + SPENDING_CUT_LIMIT) * cohort.expected_spending))
        spending = max(spending, min(cash, (1.0 - SPENDING_CUT_LIMIT) * cohort.expected_spending))
    priced = with_quality_reach(priced, basket, quality_reach(spending, floor_cost))
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
            if stationary_durables and good in specs and specs[good].service_life_years > 0.0 and flow > 0.0:
                ratio = durable_stock.replacement_for_flow(stock_flow, specs[good]) / flow
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
                              for good in sorted(set(flow_by_good) | set(smoothed_flow))}
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
        ask = lender_ask.lowest_ask(HOUSEHOLD_TIME_PREFERENCE, cohort.expected_inflation,
                                    expected_loss_rate=loss_rate_of(view, cohort.agent_id, area_currency))
        funds = (FundsOffer(cohort.agent_id, area_currency, savings, ask),)
    return AgentOrders(bids=tuple(bids), offers=offers, funds_offers=funds)
