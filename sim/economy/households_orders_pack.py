"""The year's cohort orders over arrays: baskets packed once each, every cohort ordered in one kernel call, the answer unpacked into bids.

`households_orders_kernel.year_orders` makes the orders `households_orders.goods_orders` and `year_goods.less_what_it_grew` make
(`cohort_orders` calls this and keeps the old functions for a basket the kernel does not cover: a need with share limits).
A basket's needs, goods and store goods are the same for every cohort that shares a basket key (tile, hearth, hired work, milled
grains), so they are packed once per key (a template); each cohort adds its holdings, its plot's units and its cash and income."""
from typing import Dict, List

import numpy as np

from sim.world import need_basket

from . import households_buffer_stock, households_store, lender_ask, opening_demand
from . import households_orders_kernel as kernel
from .household_time_preference import HOUSEHOLD_TIME_PREFERENCE
from .protocols import AgentOrders
from .households_bid_rows import cohort_bid_rows
from .types import FundsOffer


def covered(priced) -> bool:
    """Whether the kernel makes these priced needs' orders (share limits re-mix the needs by a search it does not run)."""
    return not any(need.spec.share_limits for need in priced)


class _Template:
    """One basket at one tile's prices: the strings and prices a bid needs, and where its rows sit in the packed arrays."""

    def __init__(self, index, row0, store0, unit0, cohort, basket, priced, weights, store_prices, view, area_currency, orders) -> None:
        tile = cohort.tile
        self.index = index
        self.row0 = row0
        self.store0 = store0
        self.unit0 = unit0
        self.substitution = basket.substitution
        self.area_currency = area_currency
        self.row_goods: List[str] = []
        self.row_areas: List[str] = []
        self.row_prices: List[float] = []
        self.row_priority: List[int] = []
        for need in priced:
            priority = 0 if need.spec.subsistence_per_person > 0.0 else 1
            for good, price, _effect, _share in need.goods:
                self.row_goods.append(good)
                self.row_areas.append(view.area_of(good, tile))
                self.row_prices.append(price)
                self.row_priority.append(priority)
        self.order_local = sorted(range(len(self.row_goods)), key=lambda row: (self.row_goods[row], row))
        self.weights = weights
        self.store_prices = store_prices
        self.store_goods = list(weights)
        self.store_areas = [view.area_of(good, tile) for good in self.store_goods]
        book = orders.book
        self.row_good_ids = [book.good_number(good) for good in self.row_goods]
        self.row_market_ids = orders.market_ids(self.row_goods, self.row_areas)
        self.store_good_ids = [book.good_number(good) for good in self.store_goods]
        self.store_market_ids = orders.market_ids(self.store_goods, self.store_areas)
        self.unit_need_ids = [need.need_id for need in basket.needs]


class _Arrays:
    """The lists the packed arrays are made from, grown as templates and cohorts are added."""

    def __init__(self) -> None:
        self.goods: Dict[str, int] = {}
        self.need_floats: List[list] = []
        self.need_ints: List[list] = []
        self.row_floats: List[list] = []
        self.row_ints: List[list] = []
        self.store_floats: List[list] = []
        self.store_ints: List[int] = []
        self.unit_floor: List[float] = []
        self.order: List[int] = []
        self.template_ints: List[list] = []
        self.template_floats: List[list] = []
        self.row_good_ids: List[int] = []         # per packed row: the book's id of its good and the order tables' id of its market
        self.row_market_ids: List[int] = []
        self.row_priorities: List[int] = []
        self.row_prices: List[float] = []
        self.store_good_ids: List[int] = []
        self.store_market_ids: List[int] = []
        self.store_prices: List[float] = []
        self.template_stores: List[int] = []
        self.order_ptr: List[int] = [0]
        self.order_flat: List[int] = []

    def good_index(self, good) -> int:
        found = self.goods.get(good)
        if found is None:
            found = self.goods[good] = len(self.goods)
        return found

    def add_template(self, index, cohort, basket, priced, shared_store, view, specs, orders) -> _Template:
        weights, store_prices, _held = households_store.store_holding(cohort, view, specs, priced, shared_store)
        first_good = priced[0].goods[0][0]
        area_currency = view.currency_of(view.area_of(first_good, cohort.tile))
        rate = view.interest_rate(area_currency)
        template = _Template(index, len(self.row_floats), len(self.store_floats), len(self.unit_floor), cohort, basket, priced, weights,
                             store_prices, view, area_currency, orders)
        need0 = len(self.need_floats)
        first_unit: Dict[str, int] = {}
        for position, need in enumerate(basket.needs):
            self.unit_floor.append(need.subsistence_per_person)
            for good, _effect in need.goods:
                first_unit.setdefault(good, position)
        for need in priced:
            qualities = dict(need.spec.qualities)
            limit = need_basket.satiation_limit(basket, need.spec.need_id, need.spec.subsistence_per_person)
            ceilings = need.ceilings or need_basket.price_ceilings(need.goods)
            self.need_ints.append([len(self.row_floats), len(self.row_floats) + len(need.goods)])
            self.need_floats.append([need.price_index, need.spec.subsistence_per_person, need.spec.budget_weight,
                                     np.nan if limit is None else limit, 1.0 if need.spec.subsistence_per_person > 0.0 else 0.0,
                                     1.0 if need.spec.qualities else 0.0])
            for (good, price, effect, share), ceiling in zip(need.goods, ceilings):
                spec = specs.get(good)
                self.row_floats.append([price, effect, share, ceiling, qualities.get(good, 1.0), 0.0,
                                        spec.service_life_years if spec is not None else 0.0,
                                        spec.spoilage_per_year if spec is not None else 0.0, 0.0])
                self.row_ints.append([self.good_index(good), first_unit.get(good, -1)])
        self.order.extend(template.row0 + row for row in template.order_local)
        self.row_good_ids.extend(template.row_good_ids)
        self.row_market_ids.extend(template.row_market_ids)
        self.row_priorities.extend(template.row_priority)
        self.row_prices.extend(template.row_prices)
        self.store_good_ids.extend(template.store_good_ids)
        self.store_market_ids.extend(template.store_market_ids)
        self.store_prices.extend(template.store_prices[good] for good in template.store_goods)
        self.template_stores.append(len(template.store_goods))
        self.order_flat.extend(template.order_local)
        self.order_ptr.append(len(self.order_flat))
        for good, weight in weights.items():
            self.store_floats.append([weight, store_prices[good], 0.0, 0.0, specs[good].service_life_years])
            self.store_ints.append(self.good_index(good))
        self.template_ints.append([need0, len(self.need_floats), template.row0, len(self.row_floats), template.store0, len(self.store_floats),
                                   template.unit0, 0 if rate is None else 1])
        self.template_floats.append([0.0 if rate is None else rate, basket.substitution])
        return template


def kernel_orders(view, specs, entries, smooth_rise: bool, key_of, store_of, orders):
    """The orders of each cohort of `entries` (cohort, basket, priced needs, cash to spend, income, units its plot grew).
    `key_of(cohort)` names the basket a cohort shares with others, `store_of(cohort)` is the dict their store weights are kept in.
    Returns (offers and savings of each cohort as `AgentOrders` with no bids, by cohort id; the cohorts' bid rows ready for
    `orders.append_bids`; each cohort's planned spending by cohort id). No `Bid` is made: `orders` is the book of orders whose ids
    the rows are numbered with."""
    arrays = _Arrays()
    templates: Dict[tuple, _Template] = {}
    cohort_floats, cohort_ints, held_rows, held_stores, grown = [], [], [], [], []
    placed = []
    stock = view.stock
    for cohort, basket, priced, cash, income, grown_units in entries:
        key = key_of(cohort)
        template = templates.get(key)
        if template is None:
            template = templates[key] = arrays.add_template(len(templates), cohort, basket, priced, store_of(cohort), view, specs, orders)
        agent, tile = cohort.agent_id, cohort.tile
        row_out, store_out, grown0 = len(held_rows), len(held_stores), len(grown)
        held_rows.extend([stock(agent, good, tile) for good in template.row_goods])
        held_stores.extend([stock(agent, good, tile) for good in template.store_goods])
        grown.extend([grown_units.get(need_id, 0.0) for need_id in template.unit_need_ids] if grown_units else [0.0] * len(template.unit_need_ids))
        cohort_floats.append([cohort.people, cohort.expected_spending, cohort.expected_floor_cost, cohort.expected_inflation, cohort.cash_target,
                              households_buffer_stock.share_wealth_carried(cohort.share_wealth, view.equity(agent)),
                              view.claims(agent, template.area_currency), cash, income, cohort.last_year_income])
        cohort_ints.append([template.index, row_out, store_out, grown0])
        placed.append((cohort, template, row_out, store_out, max(0.0, cash)))
    if not placed:
        return {}, None, {}
    row_out = np.zeros((len(held_rows), kernel.RO_COUNT))
    store_out = np.zeros((len(held_stores), kernel.SO_COUNT))
    cohort_out = np.zeros((len(placed), kernel.CA_COUNT))
    kernel.year_orders(
        smooth_rise, opening_demand.constants(), np.array(cohort_floats, dtype=np.float64).reshape(-1, kernel.CO_COUNT),
        np.array(cohort_ints, dtype=np.int64).reshape(-1, kernel.CT_COUNT), np.array(arrays.template_ints, dtype=np.int64).reshape(-1, kernel.TM_COUNT),
        np.array(arrays.template_floats, dtype=np.float64).reshape(-1, kernel.TF_COUNT), np.array(arrays.need_floats, dtype=np.float64).reshape(-1, 6),
        np.array(arrays.need_ints, dtype=np.int64).reshape(-1, 2), np.array(arrays.row_floats, dtype=np.float64).reshape(-1, 9),
        np.array(arrays.row_ints, dtype=np.int64).reshape(-1, 2), np.array(arrays.store_floats, dtype=np.float64).reshape(-1, 5),
        np.array(arrays.store_ints, dtype=np.int64), np.array(arrays.unit_floor, dtype=np.float64), np.array(arrays.order, dtype=np.int64),
        np.array(held_rows, dtype=np.float64), np.array(held_stores, dtype=np.float64), np.array(grown, dtype=np.float64), len(arrays.goods),
        row_out, store_out, cohort_out)
    bid_rows = cohort_bid_rows(
        np.array([orders.book.agent_number(cohort.agent_id) for cohort, *_rest in placed], dtype=np.int64),
        np.array([orders.book.tile_number(cohort.tile) for cohort, *_rest in placed], dtype=np.int64),
        np.array([template.index for _cohort, template, *_rest in placed], dtype=np.int64),
        np.array([row_start for _cohort, _template, row_start, *_rest in placed], dtype=np.int64),
        np.array([store_start for _cohort, _template, _row_start, store_start, _cash in placed], dtype=np.int64),
        cohort_out[:, kernel.CA_PLAN].copy(), np.array(arrays.order_ptr, dtype=np.int64), np.array(arrays.order_flat, dtype=np.int64),
        np.array([template.row0 for template in templates.values()], dtype=np.int64),
        np.array([template.store0 for template in templates.values()], dtype=np.int64), np.array(arrays.template_stores, dtype=np.int64),
        np.array([template.substitution for template in templates.values()], dtype=np.float64),
        np.array(arrays.row_good_ids, dtype=np.int64), np.array(arrays.row_market_ids, dtype=np.int64),
        np.array(arrays.row_priorities, dtype=np.int64), np.array(arrays.row_prices, dtype=np.float64),
        np.array(arrays.store_good_ids, dtype=np.int64), np.array(arrays.store_market_ids, dtype=np.int64),
        np.array(arrays.store_prices, dtype=np.float64), row_out, store_out)
    stores, answers = store_out.tolist(), cohort_out.tolist()
    made = {cohort.agent_id: _orders_of(cohort, template, stores, store_start, answers[position], cash, view, specs)
            for position, (cohort, template, _row_start, store_start, cash) in enumerate(placed)}
    planned = {cohort.agent_id: total for (cohort, *_rest), total in zip(placed, bid_rows[6].tolist())}
    return made, bid_rows[:6], planned


def _orders_of(cohort, template, stores, store_start, answer, cash, view, specs) -> AgentOrders:
    """A cohort's store offers and savings (its bids are rows)."""
    agent = cohort.agent_id
    offers = ()
    if answer[kernel.CA_PLAN] > 0.0:
        held = {good: stores[store_start + local][2] for local, good in enumerate(template.store_goods)}
        if any(held[good] > 0.0 for good in held):
            offers = tuple(households_store.store_offers(cohort, view, specs, template.weights, template.store_prices, held,
                                                         answer[kernel.CA_ABOVE_BUFFER], answer[kernel.CA_REAL_RATE], cash,
                                                         answer[kernel.CA_FLOOR_COST]))
    funds = ()
    if answer[kernel.CA_SAVINGS] > 0.0:
        ask = lender_ask.lowest_ask(HOUSEHOLD_TIME_PREFERENCE, cohort.expected_inflation,
                                    expected_loss_rate=view.loss_rate(agent, template.area_currency))
        funds = (FundsOffer(agent, template.area_currency, answer[kernel.CA_SAVINGS], ask),)
    return AgentOrders(offers=offers, funds_offers=funds)
