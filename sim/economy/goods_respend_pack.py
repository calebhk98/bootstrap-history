"""The respend rounds' records packed into the arrays of goods_respend_kernel.respend_rounds: the households that bid in the
first round (rows in sorted id order), their baskets flattened, the market each of their goods is bought in, every market's
offers in clearing order, and the purses and stocks of the agents and (agent, tile) keys the markets touch.
"""
import itertools
from dataclasses import dataclass
from typing import Dict, List

import numpy

from sim.constants import declare

from .goods_production import read_stocks
from .goods_respend_rows import Interner, bid_rows, bought_columns, offer_rows, table_columns
from .goods_respend import need_of_good
from .types import is_edge, is_external_edge
from .view_areas import areas_in



@dataclass
class Packed:
    """What the kernel is given (`arguments`, by the kernel's parameter names, in its order) and what unpacking needs."""
    arguments: Dict[str, object]
    market_keys: list         # (good, area) per market row, sorted
    goods: list               # good id per good index
    buyers: list              # household id per buyer row
    baskets: list             # the Basket object per basket index
    buyer_tile: list
    agents: list              # agent id per agent index
    keys: list                # (agent index, good index, tile) per key
    offer_origin: list        # per packed offer: its index in its market's original offer list


def flatten_baskets(baskets, good_index) -> tuple:
    """The baskets as arrays: needs of each (`need_ptr`), a need's budget weight, its slot in the sorted need ids, whether it
    has share limits, and the rows of its goods (`need_good_ptr`: good index, effectiveness, limit, whether limited); per
    basket one minus the substitution, the substitution, and the slot of the first need serving each good (-1: none)."""
    need_ids = sorted({spec.need_id for basket in baskets for spec in basket.needs})
    slot_of = {need_id: slot for slot, need_id in enumerate(need_ids)}
    need_ptr, weight, slots, has_limits, good_ptr = [0], [], [], [], [0]
    good_rows, effects, limits, limited = [], [], [], []
    for basket in baskets:
        for spec in basket.needs:
            weight.append(spec.budget_weight)
            slots.append(slot_of[spec.need_id])
            has_limits.append(bool(spec.share_limits))
            share_limits = dict(spec.share_limits)
            for good, effect in spec.goods:
                good_rows.append(good_index[good])
                effects.append(effect)
                limited.append(good in share_limits)
                limits.append(share_limits.get(good, 0.0))
            good_ptr.append(len(good_rows))
        need_ptr.append(len(weight))
    need_of_good_slot = numpy.full((len(baskets), len(good_index)), -1, dtype=numpy.int64)
    for index, basket in enumerate(baskets):
        for good, need_id in need_of_good(basket).items():
            need_of_good_slot[index, good_index[good]] = slot_of[need_id]
    return (numpy.array(need_ptr, dtype=numpy.int64), numpy.array(weight, dtype=float), numpy.array(slots, dtype=numpy.int64),
            numpy.array(has_limits, dtype=numpy.bool_), numpy.array(good_ptr, dtype=numpy.int64),
            numpy.array(good_rows, dtype=numpy.int64), numpy.array(effects, dtype=float), numpy.array(limits, dtype=float),
            numpy.array(limited, dtype=numpy.bool_), numpy.array([1.0 - basket.substitution for basket in baskets]),
            numpy.array([basket.substitution for basket in baskets]), need_of_good_slot, len(need_ids))


def pack(setup, record, view, ledger, markets, basket_of, orders=None) -> "Packed":
    """Pack `markets` ({(good, area): LeftMarket}) and the households that bid in them; None when no household bid. The bids and the offers
    are read as columns (goods_respend_rows.py)."""
    households = record.cohorts
    market_keys = markets.sorted_keys() if hasattr(markets, "sorted_keys") else sorted(markets)
    market_index = {key: index for index, key in enumerate(market_keys)}
    agents_interned, tiles_interned = Interner(), Interner()
    columns = table_columns(markets, market_keys) if orders is not None else None
    bids = bid_rows(markets, market_keys, orders, agents_interned, columns)
    is_household = numpy.array([name in households for name in agents_interned.names], dtype=numpy.bool_)
    household_entry = is_household[bids.buyer] if len(bids.buyer) else numpy.zeros(0, dtype=numpy.bool_)
    buyer_ids = sorted({agents_interned.names[each] for each in numpy.unique(bids.buyer[household_entry]).tolist()})
    if not buyer_ids or not market_keys:
        return None
    row_of_id = numpy.full(max(len(agents_interned.names), 1), -1, dtype=numpy.int64)
    for row, buyer in enumerate(buyer_ids):
        row_of_id[agents_interned.ids[buyer]] = row
    baskets: List[object] = []
    basket_number: Dict[int, int] = {}
    buyer_basket = numpy.zeros(len(buyer_ids), dtype=numpy.int64)
    for row, buyer in enumerate(buyer_ids):
        basket = basket_of(households[buyer])
        if id(basket) not in basket_number:
            basket_number[id(basket)] = len(baskets)
            baskets.append(basket)
        buyer_basket[row] = basket_number[id(basket)]
    goods = sorted({key[0] for key in market_keys} | {good for basket in baskets for spec in basket.needs
                                                      for good, _effect in spec.goods})
    good_index = {good: index for index, good in enumerate(goods)}
    flat = flatten_baskets(baskets, good_index)
    area_rows: Dict[tuple, int] = {}
    area_table: List[list] = []
    buyer_area_row = numpy.zeros(len(buyer_ids), dtype=numpy.int64)
    buyer_tile = []
    for row, buyer in enumerate(buyer_ids):
        tile = households[buyer].tile
        buyer_tile.append(tile)
        slot = (tile, int(buyer_basket[row]))
        if slot not in area_rows:
            area_rows[slot] = len(area_table)
            table = [-1] * len(goods)
            wanted = list(need_of_good(baskets[slot[1]]))
            for good, market in zip(wanted, map(market_index.get, zip(wanted, areas_in(view, wanted, tile)), itertools.repeat(-1))):
                table[good_index[good]] = market
            area_table.append(table)
        buyer_area_row[row] = area_rows[slot]
    area_market = numpy.array(area_table, dtype=numpy.int64).reshape(len(area_table), len(goods))

    offers = offer_rows(markets, market_keys, orders, agents_interned, tiles_interned, columns)
    buyer_id = numpy.array([agents_interned.ids[buyer] for buyer in buyer_ids], dtype=numpy.int64)
    used_ids = numpy.unique(numpy.concatenate((buyer_id, offers.seller)))
    agents = sorted(agents_interned.names[each] for each in used_ids.tolist())
    agent_of_id = numpy.full(len(agents_interned.names), -1, dtype=numpy.int64)
    agent_of_id[[agents_interned.ids[name] for name in agents]] = numpy.arange(len(agents), dtype=numpy.int64)
    tile_of_buyer = numpy.array([tiles_interned.of(tile) for tile in buyer_tile], dtype=numpy.int64)
    good_of_market = numpy.array([good_index[key[0]] for key in market_keys], dtype=numpy.int64)
    offer_ptr = numpy.concatenate(([0], numpy.cumsum(numpy.bincount(offers.market, minlength=len(market_keys))))).astype(numpy.int64)
    stock_code = (agent_of_id[offers.seller] * len(goods) + good_of_market[offers.market]) * max(len(tiles_interned.names), 1) + offers.tile
    distinct_code, first_place, inverse = numpy.unique(stock_code, return_index=True, return_inverse=True)
    by_appearance = numpy.argsort(first_place, kind="stable")
    key_of_distinct = numpy.empty(len(distinct_code), dtype=numpy.int64)
    key_of_distinct[by_appearance] = numpy.arange(len(distinct_code), dtype=numpy.int64)
    offer_key = key_of_distinct[inverse]
    key_places = first_place[by_appearance]
    key_agent = agent_of_id[offers.seller[key_places]]
    key_good = good_of_market[offers.market[key_places]]
    keys = list(zip(key_agent.tolist(), key_good.tolist(), [tiles_interned.names[each] for each in offers.tile[key_places].tolist()]))
    offer_agent = agent_of_id[offers.seller]
    offer_origin = offers.origin.tolist()
    book = record.book
    currency = setup.currency_id
    key_stock = numpy.array(read_stocks(book, [(agents[agent], goods[good], tile) for agent, good, tile in keys]), dtype=float)
    agent_cash = book.balances_of(agents, currency)
    buyer_key = numpy.full((len(buyer_ids), len(goods)), -1, dtype=numpy.int64)
    wanted_cell = area_market[buyer_area_row] >= 0
    buyer_code = (agent_of_id[buyer_id][:, None] * len(goods) + numpy.arange(len(goods), dtype=numpy.int64)[None, :]) \
        * max(len(tiles_interned.names), 1) + tile_of_buyer[:, None]
    if len(distinct_code):
        place = numpy.minimum(numpy.searchsorted(distinct_code, buyer_code), len(distinct_code) - 1)
        match = wanted_cell & (distinct_code[place] == buyer_code)
        buyer_key[match] = key_of_distinct[place[match]]
    market_good = good_of_market

    has_bid = numpy.zeros((len(market_keys), len(buyer_ids)), dtype=numpy.bool_)
    if columns is not None:
        first_price = columns.year_markets.table.first_price[columns.cells]
        fallback_ok = ~numpy.isnan(first_price)
        fallback = numpy.where(fallback_ok, first_price, 0.0)
    else:
        fallback = numpy.zeros(len(market_keys))
        fallback_ok = numpy.zeros(len(market_keys), dtype=numpy.bool_)
        for index, key in enumerate(market_keys):
            price = markets[key].result.price
            if price is not None:
                fallback[index] = price
                fallback_ok[index] = True
    units, money = bought_columns(markets, market_keys, bids, agents_interned, len(orders.book.agent_ids.name_list) if orders is not None else 0, columns)
    mine = numpy.flatnonzero(household_entry)
    entry_row = row_of_id[bids.buyer[mine]]
    entry_market = bids.market[mine]
    has_bid[entry_market, entry_row] = True
    flexible, reference, elasticity = bids.flexible[mine], bids.reference[mine], bids.elasticity[mine]
    kept = (bids.budget[mine] > 0.0) & (flexible > 0.0) & (reference > 0.0)
    flexible, reference, elasticity = numpy.where(kept, flexible, 0.0), numpy.where(kept, reference, 1.0), numpy.where(kept, elasticity, 0.0)
    order = numpy.lexsort((entry_row, entry_market))
    first = [entry_market[order], entry_row[order], bids.floor[mine][order], flexible[order], reference[order], -elasticity[order],
             bids.budget[mine][order], bids.maximum[mine][order], units[mine][order], money[mine][order]]
    if columns is not None:
        remembered = columns.year_markets.table.last_price[columns.cells]
        has_last = ~numpy.isnan(remembered)
        last_price = numpy.where(has_last, remembered, 0.0)
    else:
        last_prices = [markets[key].last_price for key in market_keys]
        has_last = numpy.array([price is not None for price in last_prices], dtype=numpy.bool_)
        last_price = numpy.array([0.0 if price is None else price for price in last_prices])
    edge = numpy.array([is_edge(agent) for agent in agents], dtype=numpy.bool_)
    external = numpy.array([is_external_edge(agent) for agent in agents], dtype=numpy.bool_)
    importing = numpy.array([agent in ledger.import_accounts for agent in agents], dtype=numpy.bool_)
    exporting = numpy.array([agent in ledger.export_accounts for agent in agents], dtype=numpy.bool_)
    max_goods = max(len(need_of_good(basket)) for basket in baskets)
    reservation = offers.reservation
    quantity = offers.quantity
    offer_order = numpy.lexsort((offers.origin, offers.market)).astype(numpy.int64)
    names = ("buyer_agent", "buyer_basket", "buyer_area_row", "buyer_key", "has_bid", "area_market", "need_ptr", "need_weight",
             "need_slot", "need_has_limits", "need_good_ptr", "goods", "effects", "limits", "limited", "basket_exponent",
             "basket_substitution", "basket_need_of_good", "need_count", "max_goods", "market_good", "offer_ptr",
             "offer_reservation", "offer_quantity", "offer_key", "offer_agent", "offer_order", "market_last_price", "market_has_last",
             "market_fallback", "market_fallback_ok", "key_stock", "key_agent", "agent_cash", "agent_edge",
             "agent_external", "agent_import", "agent_export", "first_market", "first_buyer", "first_floor",
             "first_flexible", "first_reference", "first_exponent", "first_budget", "first_maximum", "first_units",
             "first_money")
    values = [agent_of_id[buyer_id], buyer_basket, buyer_area_row,
              buyer_key, has_bid, area_market, *flat[:6], flat[6], flat[7], flat[8], flat[9], flat[10], flat[11], flat[12],
              max_goods, market_good, offer_ptr, reservation, quantity, offer_key, offer_agent, offer_order, last_price, has_last,
              fallback, fallback_ok, key_stock, key_agent, agent_cash, edge,
              external, importing, exporting, *first]
    arguments = dict(zip(names, values))
    return Packed(arguments, market_keys, goods, buyer_ids, baskets, buyer_tile, agents, keys, offer_origin)
