"""The respend rounds' records packed into the arrays of goods_respend_kernel.respend_rounds: the households that bid in the
first round (rows in sorted id order), their baskets flattened, the market each of their goods is bought in, every market's
offers in clearing order, and the purses and stocks of the agents and (agent, tile) keys the markets touch.
"""
from dataclasses import dataclass
from operator import attrgetter
from typing import Dict, List

import numpy

from sim.constants import declare

from .goods_production import read_stocks
from .goods_respend import need_of_good
from .types import is_edge, is_external_edge

_BID_FIELDS = attrgetter("floor_quantity", "flexible_quantity", "reference_price", "elasticity", "budget", "maximum_price")
OFFER_ORDER = attrgetter("reservation_price", "seller", "tile")     # goods_market.in_clearing_order


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


def _bid_fields(market, lists):
    """(buyer, floor, flexible, reference price, elasticity, budget, ceiling) of each first-round bid of the market, read from
    the table's columns where the market is on the tables."""
    if market.rows is not None:
        return [(lists.buyer[row], lists.floor_quantity[row], lists.flexible_quantity[row], lists.reference_price[row], lists.elasticity[row],
                 lists.budget[row], lists.maximum_price[row]) for row in market.rows.bid_rows]
    return [(bid.buyer, *_BID_FIELDS(bid)) for bid in market.bids]


def _offers_left(market, lists):
    """The offers left in the market, in the order `market.offers` lists them: objects, or (seller, tile, reservation, units)
    records for a market on the tables."""
    return market.rows.left_offers(lists) if market.rows is not None else list(market.offers)


def pack(setup, record, view, ledger, markets, basket_of, orders=None) -> "Packed":
    """Pack `markets` ({(good, area): LeftMarket}) and the households that bid in them; None when no household bid."""
    households = record.cohorts
    market_keys = sorted(markets)
    market_index = {key: index for index, key in enumerate(market_keys)}
    bid_lists = orders.bid_lists() if orders is not None and any(markets[key].rows is not None for key in market_keys) else None
    fields = {key: _bid_fields(markets[key], bid_lists) for key in market_keys}
    buyer_ids = sorted({each[0] for key in market_keys for each in fields[key] if each[0] in households})
    if not buyer_ids or not market_keys:
        return None
    row_of = {buyer: row for row, buyer in enumerate(buyer_ids)}
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
            for good in need_of_good(baskets[slot[1]]):
                table[good_index[good]] = market_index.get((good, view.area_of(good, tile)), -1)
            area_table.append(table)
        buyer_area_row[row] = area_rows[slot]
    area_market = numpy.array(area_table, dtype=numpy.int64).reshape(len(area_table), len(goods))

    agent_names = {buyer for buyer in buyer_ids}
    offer_lists = []
    left_lists = orders.offer_lists() if bid_lists is not None else None
    records = {key: _offers_left(markets[key], left_lists) for key in market_keys}
    for key in market_keys:
        ordered = sorted((offer for offer in records[key] if offer.quantity > 0.0), key=OFFER_ORDER)
        offer_lists.append(ordered)
        agent_names.update(offer.seller for offer in ordered)
    agents = sorted(agent_names)
    agent_index = {agent: index for index, agent in enumerate(agents)}
    key_index: Dict[tuple, int] = {}
    keys: List[tuple] = []
    offer_ptr, reservation, quantity, offer_key, offer_agent, offer_origin, offer_ids = [0], [], [], [], [], [], []
    for key, ordered in zip(market_keys, offer_lists):
        position = {id(offer): index for index, offer in enumerate(records[key])}
        for offer in ordered:
            stock_key = (agent_index[offer.seller], good_index[key[0]], offer.tile)
            if stock_key not in key_index:
                key_index[stock_key] = len(keys)
                keys.append(stock_key)
            reservation.append(offer.reservation_price)
            quantity.append(offer.quantity)
            offer_key.append(key_index[stock_key])
            offer_agent.append(agent_index[offer.seller])
            offer_origin.append(position[id(offer)])
            offer_ids.append((offer.seller, offer.tile))
        offer_ptr.append(len(reservation))
    book = record.book
    currency = setup.currency_id
    key_stock = numpy.array(read_stocks(book, [(agents[agent], goods[good], tile) for agent, good, tile in keys]), dtype=float)
    agent_cash = book.balances_of(agents, currency)
    buyer_key = numpy.full((len(buyer_ids), len(goods)), -1, dtype=numpy.int64)
    for row, buyer in enumerate(buyer_ids):
        for good in range(len(goods)):
            if area_market[buyer_area_row[row], good] >= 0:
                buyer_key[row, good] = key_index.get((agent_index[buyer], good, buyer_tile[row]), -1)
    market_good = numpy.array([good_index[key[0]] for key in market_keys], dtype=numpy.int64)

    has_bid = numpy.zeros((len(market_keys), len(buyer_ids)), dtype=numpy.bool_)
    rows = []
    fallback = numpy.zeros(len(market_keys))
    fallback_ok = numpy.zeros(len(market_keys), dtype=numpy.bool_)
    for index, key in enumerate(market_keys):
        market = markets[key]
        if market.result.price is not None:
            fallback[index] = market.result.price
            fallback_ok[index] = True
        for buyer, floor, flexible, reference, elasticity, budget, maximum in fields[key]:
            row = row_of.get(buyer)
            if row is None:
                continue
            has_bid[index, row] = True
            if not (budget > 0.0 and flexible > 0.0 and reference > 0.0):
                flexible, reference, elasticity = 0.0, 1.0, 0.0
            units, money = market.bought.get(buyer, (0.0, 0.0))
            rows.append((index, row, floor, flexible, reference, -elasticity, budget, maximum, units, money))
    table = numpy.array(rows, dtype=float).reshape(-1, 10)
    order = numpy.lexsort((table[:, 1], table[:, 0]))
    table = table[order]
    first = [table[:, 0].astype(numpy.int64), table[:, 1].astype(numpy.int64)] + [table[:, column].copy()
                                                                                    for column in range(2, 10)]
    last_prices = [markets[key].last_price for key in market_keys]
    has_last = numpy.array([price is not None for price in last_prices], dtype=numpy.bool_)
    last_price = numpy.array([0.0 if price is None else price for price in last_prices])
    edge = numpy.array([is_edge(agent) for agent in agents], dtype=numpy.bool_)
    external = numpy.array([is_external_edge(agent) for agent in agents], dtype=numpy.bool_)
    importing = numpy.array([agent in ledger.import_accounts for agent in agents], dtype=numpy.bool_)
    exporting = numpy.array([agent in ledger.export_accounts for agent in agents], dtype=numpy.bool_)
    max_goods = max(len(need_of_good(basket)) for basket in baskets)
    offer_ptr = numpy.array(offer_ptr, dtype=numpy.int64)
    offer_agent = numpy.array(offer_agent, dtype=numpy.int64)
    offer_key = numpy.array(offer_key, dtype=numpy.int64)
    reservation = numpy.array(reservation)
    offer_order = numpy.array([first + position for first, last in zip(offer_ptr[:-1].tolist(), offer_ptr[1:].tolist())
                               for position in sorted(range(last - first), key=lambda each: offer_origin[first + each])],
                              dtype=numpy.int64)
    quantity = numpy.array(quantity)
    names = ("buyer_agent", "buyer_basket", "buyer_area_row", "buyer_key", "has_bid", "area_market", "need_ptr", "need_weight",
             "need_slot", "need_has_limits", "need_good_ptr", "goods", "effects", "limits", "limited", "basket_exponent",
             "basket_substitution", "basket_need_of_good", "need_count", "max_goods", "market_good", "offer_ptr",
             "offer_reservation", "offer_quantity", "offer_key", "offer_agent", "offer_order", "market_last_price", "market_has_last",
             "market_fallback", "market_fallback_ok", "key_stock", "key_agent", "agent_cash", "agent_edge",
             "agent_external", "agent_import", "agent_export", "first_market", "first_buyer", "first_floor",
             "first_flexible", "first_reference", "first_exponent", "first_budget", "first_maximum", "first_units",
             "first_money")
    values = [numpy.array([agent_index[buyer] for buyer in buyer_ids], dtype=numpy.int64), buyer_basket, buyer_area_row,
              buyer_key, has_bid, area_market, *flat[:6], flat[6], flat[7], flat[8], flat[9], flat[10], flat[11], flat[12],
              max_goods, market_good, offer_ptr, reservation, quantity, offer_key, offer_agent, offer_order, last_price, has_last,
              fallback, fallback_ok, key_stock, numpy.array([key[0] for key in keys], dtype=numpy.int64), agent_cash, edge,
              external, importing, exporting, *first]
    arguments = dict(zip(names, values))
    return Packed(arguments, market_keys, goods, buyer_ids, baskets, buyer_tile, agents, keys, offer_origin)
