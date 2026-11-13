"""The year's cohort orders over arrays: baskets packed once each, every cohort ordered in one kernel call, the answer unpacked into bids.

`households_orders_kernel.year_orders` makes the orders `households_orders.goods_orders` and `year_goods.less_what_it_grew` make
(`cohort_orders` calls this for every cohort; the old functions stay for the opening and the tests).
A basket's needs, goods and store goods are the same for every cohort that shares a basket key (tile, hearth, hired work, milled
grains), so they are packed once per key (a template); each cohort adds its holdings, its plot's units and its cash and income."""
from typing import Dict, List

import numpy as np

from sim.world import need_basket

from . import households_buffer_stock, households_store, households_template, lender_ask, opening_demand
from . import households_orders_kernel as kernel
from . import opening_demand_kernel as opening_kernel
from .household_time_preference import HOUSEHOLD_TIME_PREFERENCE
from .priced_need_list import priced_needs_of
from .priced_need_tables import GOODS, basket_rows
from .protocols import AgentOrders
from .households_bid_rows import cohort_bid_rows
from .stock_block import stock_block
from .types import FundsOffer


class _Template:
    """One basket at one tile's prices: the strings and ids a bid needs, and where its rows sit in the packed arrays."""

    def __init__(self, index, row0, store0, unit0, cohort, basket, rows, static, store_static, weights, store_prices, area_currency) -> None:
        self.index = index
        self.row0 = row0
        self.store0 = store0
        self.unit0 = unit0
        self.substitution = basket.substitution
        self.area_currency = area_currency
        self.order_local = rows.order
        self.weights = weights
        self.store_prices = store_prices
        self.store_goods = store_static.goods
        self.row_good_ids = static.good_ids
        self.row_market_ids = static.market_ids
        self.store_good_ids = store_static.good_ids
        self.store_areas = dict(zip(store_static.goods, store_static.areas))      # the market area of each store good at the tile
        self.store_market_ids = store_static.market_ids
        self.unit_need_ids = [need.need_id for need in basket.needs]


def _joined(blocks: list, columns: int, dtype) -> np.ndarray:
    """The blocks (arrays of `columns` columns, or of one dimension when `columns` is 0) one after another."""
    if blocks:
        return np.concatenate(blocks)
    return np.zeros((0, columns) if columns else 0, dtype=dtype)


class _Arrays:
    """The blocks the packed arrays are made from, grown as templates and cohorts are added."""

    def __init__(self, specs) -> None:
        self.local = households_template.LocalGoods()
        self.storable = households_store.storable_goods(specs)
        self.static: Dict[tuple, households_template.StaticRows] = {}
        self.life = np.array([specs[good].service_life_years if good in specs else 0.0 for good in GOODS.names], dtype=np.float64)
        self.spoilage = np.array([specs[good].spoilage_per_year if good in specs else 0.0 for good in GOODS.names], dtype=np.float64)
        self.need_floats: List[list] = []
        self.need_ints: List[np.ndarray] = []
        self.row_floats: List[np.ndarray] = []
        self.row_ints: List[np.ndarray] = []
        self.store_floats: List[list] = []
        self.store_ints: List[int] = []
        self.unit_floor: List[float] = []
        self.order: List[np.ndarray] = []
        self.template_ints: List[list] = []
        self.template_floats: List[list] = []
        self.row_good_ids: List[int] = []         # per packed row: the book's id of its good and the order tables' id of its market
        self.row_market_ids: List[int] = []
        self.row_priorities: List[np.ndarray] = []
        self.row_prices: List[np.ndarray] = []
        self.store_good_ids: List[int] = []
        self.store_market_ids: List[int] = []
        self.store_prices: List[float] = []
        self.template_stores: List[int] = []
        self.order_ptr: List[int] = [0]
        self.order_flat: List[np.ndarray] = []
        self.row_count = 0

    def add_template(self, index, cohort, basket, priced, shared_store, view, specs, orders) -> _Template:
        priced = priced_needs_of(priced)
        weights, store_prices = households_store.store_weights_of(cohort.tile, view, specs, priced, shared_store, self.storable)
        columns, tile = priced.columns, cohort.tile
        first_good = columns.names[columns.start[priced.positions[0]]]
        area_currency = view.currency_of(view.area_of(first_good, tile))
        rate = view.interest_rate(area_currency)
        blocks = list(priced.blocks())
        _held, _specs, first_of_need, basket_goods, *_rest = basket_rows(basket.needs)
        counts_per_need = np.diff(np.array(first_of_need + [len(basket_goods)], dtype=np.int64))
        first_unit = households_template.first_unit_of_goods(basket_goods, np.repeat(np.arange(len(counts_per_need)), counts_per_need).tolist())
        rows = households_template.template_rows(priced, [spec.subsistence_per_person > 0.0 for spec, *_rest in blocks], first_unit,
                                                 self.life, self.spoilage, self.local)
        row_names = GOODS.name_array()[rows.good_numbers].tolist()
        static = households_template.static_rows(self.static, row_names, (tile, rows.good_numbers.tobytes()), tile, view, orders)
        store_goods = list(weights)
        store_static = households_template.static_rows(self.static, store_goods, (tile, tuple(store_goods)), tile, view, orders)
        row0, store0, unit0, need0 = self.row_count, len(self.store_floats), len(self.unit_floor), len(self.need_floats)
        template = _Template(index, row0, store0, unit0, cohort, basket, rows, static, store_static, weights, store_prices, area_currency)
        self.unit_floor.extend(spec.subsistence_per_person for spec in basket.needs)
        ends = row0 + np.cumsum(rows.counts)
        self.need_ints.append(np.stack([ends - rows.counts, ends], axis=1) if len(ends) else np.zeros((0, 2), dtype=np.int64))
        for spec, price_index, _first, _end in blocks:
            limit = need_basket.satiation_limit(basket, spec.need_id, spec.subsistence_per_person)
            self.need_floats.append([price_index, spec.subsistence_per_person, spec.budget_weight, np.nan if limit is None else limit,
                                     1.0 if spec.subsistence_per_person > 0.0 else 0.0, 1.0 if spec.qualities else 0.0])
        self.row_floats.append(rows.floats)
        self.row_ints.append(np.stack([rows.local_goods, rows.first_unit], axis=1))
        self.row_count += len(rows.local_goods)
        self.order.append(row0 + rows.order)
        self.row_good_ids.extend(template.row_good_ids)
        self.row_market_ids.extend(template.row_market_ids)
        self.row_priorities.append(rows.priority)
        self.row_prices.append(rows.floats[:, 0])
        self.store_good_ids.extend(template.store_good_ids)
        self.store_market_ids.extend(template.store_market_ids)
        self.store_prices.extend(template.store_prices[good] for good in template.store_goods)
        self.template_stores.append(len(template.store_goods))
        self.order_flat.append(rows.order)
        self.order_ptr.append(self.order_ptr[-1] + len(rows.order))
        if weights:
            for good, weight in weights.items():
                self.store_floats.append([weight, store_prices[good], 0.0, 0.0, specs[good].service_life_years])
            self.store_ints.extend(self.local.of(np.array([GOODS.of(good) for good in weights], dtype=np.int64)).tolist())
        self.template_ints.append([need0, len(self.need_floats), row0, self.row_count, store0, len(self.store_floats),
                                   unit0, 0 if rate is None else 1])
        self.template_floats.append([0.0 if rate is None else rate, basket.substitution])
        return template


def kernel_orders(view, specs, entries, smooth_rise: bool, key_of, store_of, orders):
    """The orders of each cohort of `entries` (cohort, basket, priced needs, cash to spend, income, units its plot grew).
    `key_of(cohort)` names the basket a cohort shares with others, `store_of(cohort)` is the dict their store weights are kept in.
    Returns (offers and savings of each cohort as `AgentOrders` with no bids, by cohort id; the cohorts' bid rows ready for
    `orders.append_bids`; each cohort's planned spending by cohort id). No `Bid` is made: `orders` is the book of orders whose ids
    the rows are numbered with."""
    arrays = _Arrays(specs)
    templates: Dict[tuple, _Template] = {}
    cohort_floats, cohort_ints, grown = [], [], []
    row_cells, store_cells = ([], [], []), ([], [], [])        # (agent number, good number, tile number) of every packed holding
    placed = []
    for cohort, basket, priced, cash, income, grown_units in entries:
        key = key_of(cohort)
        template = templates.get(key)
        if template is None:
            template = templates[key] = arrays.add_template(len(templates), cohort, basket, priced, store_of(cohort), view, specs, orders)
        agent, tile = cohort.agent_id, cohort.tile
        agent_number, tile_number = orders.agent_id(agent), orders.tile_id(tile)
        row_out, store_out, grown0 = len(row_cells[0]), len(store_cells[0]), len(grown)
        for (agents, goods, tiles), good_ids in ((row_cells, template.row_good_ids), (store_cells, template.store_good_ids)):
            agents.extend([agent_number] * len(good_ids))
            goods.extend(good_ids)
            tiles.extend([tile_number] * len(good_ids))
        grown.extend([grown_units.get(need_id, 0.0) for need_id in template.unit_need_ids] if grown_units else [0.0] * len(template.unit_need_ids))
        cohort_floats.append([cohort.people, cohort.expected_spending, cohort.expected_floor_cost, cohort.expected_inflation, cohort.cash_target,
                              households_buffer_stock.share_wealth_carried(cohort.share_wealth, view.equity(agent)),
                              view.claims(agent, template.area_currency), cash, income, cohort.last_year_income])
        cohort_ints.append([template.index, row_out, store_out, grown0])
        placed.append((cohort, template, row_out, store_out, max(0.0, cash)))
    if not placed:
        return {}, None, {}
    held_rows, held_stores = stock_block(orders.book, *row_cells), stock_block(orders.book, *store_cells)    # one block read of the book each
    row_out = np.zeros((len(held_rows), kernel.RO_COUNT))
    store_out = np.zeros((len(held_stores), kernel.SO_COUNT))
    cohort_out = np.zeros((len(placed), kernel.CA_COUNT))
    kernel.year_orders(
        smooth_rise, opening_demand.constants(), np.array(cohort_floats, dtype=np.float64).reshape(-1, kernel.CO_COUNT),
        np.array(cohort_ints, dtype=np.int64).reshape(-1, kernel.CT_COUNT), np.array(arrays.template_ints, dtype=np.int64).reshape(-1, kernel.TM_COUNT),
        np.array(arrays.template_floats, dtype=np.float64).reshape(-1, kernel.TF_COUNT), np.array(arrays.need_floats, dtype=np.float64).reshape(-1, 6),
        _joined(arrays.need_ints, 2, np.int64), _joined(arrays.row_floats, opening_kernel.RF_COUNT, np.float64),
        _joined(arrays.row_ints, 2, np.int64), np.array(arrays.store_floats, dtype=np.float64).reshape(-1, 5),
        np.array(arrays.store_ints, dtype=np.int64), np.array(arrays.unit_floor, dtype=np.float64), _joined(arrays.order, 0, np.int64),
        np.array(held_rows, dtype=np.float64), np.array(held_stores, dtype=np.float64), np.array(grown, dtype=np.float64), arrays.local.count,
        row_out, store_out, cohort_out)
    bid_rows = cohort_bid_rows(
        np.array([orders.agent_id(cohort.agent_id) for cohort, *_rest in placed], dtype=np.int64),
        np.array([orders.tile_id(cohort.tile) for cohort, *_rest in placed], dtype=np.int64),
        np.array([template.index for _cohort, template, *_rest in placed], dtype=np.int64),
        np.array([row_start for _cohort, _template, row_start, *_rest in placed], dtype=np.int64),
        np.array([store_start for _cohort, _template, _row_start, store_start, _cash in placed], dtype=np.int64),
        cohort_out[:, kernel.CA_PLAN].copy(), np.array(arrays.order_ptr, dtype=np.int64), _joined(arrays.order_flat, 0, np.int64),
        np.array([template.row0 for template in templates.values()], dtype=np.int64),
        np.array([template.store0 for template in templates.values()], dtype=np.int64), np.array(arrays.template_stores, dtype=np.int64),
        np.array([template.substitution for template in templates.values()], dtype=np.float64),
        np.array(arrays.row_good_ids, dtype=np.int64), np.array(arrays.row_market_ids, dtype=np.int64),
        _joined(arrays.row_priorities, 0, np.int64), _joined(arrays.row_prices, 0, np.float64),
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
                                                         answer[kernel.CA_FLOOR_COST], template.store_areas))
    funds = ()
    if answer[kernel.CA_SAVINGS] > 0.0:
        ask = lender_ask.lowest_ask(HOUSEHOLD_TIME_PREFERENCE, cohort.expected_inflation,
                                    expected_loss_rate=view.loss_rate(agent, template.area_currency),
                                    land_yield=view.land_yield(template.area_currency), public_premium=view.public_premium(template.area_currency))
        funds = (FundsOffer(agent, template.area_currency, answer[kernel.CA_SAVINGS], ask),)
    return AgentOrders(offers=offers, funds_offers=funds)
