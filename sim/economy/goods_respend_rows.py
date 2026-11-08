"""The first round's bids and the offers left, as columns for `goods_respend_pack.pack`: no per-bid tuple and no `LeftOffer` record for a market on
the order tables, and the market's `bought` read as columns when the settlement kept them (`goods_settle.BoughtColumns`).

A market on the tables names its rows (`goods_market_rows.MarketRows`); a market on the objects (a book edge selling, a good outside the year
arrays) is read from its `Bid` and `Offer` objects. Names are interned: `Interner` numbers each distinct name once, so a column of agent or tile
names is an integer column and the sort by name is a sort by `Interner.ranks`.

Columns of `bid_rows` (one entry per first-round bid, in market order and then in the market's arrival order):
    market      index of the market in the sorted market keys                      market index
    buyer       the buyer's interned id (`Interner.names`)                          agent id
    floor, flexible, reference, elasticity, budget, maximum   the bid's figures (`bid_columns.BidColumns`)
Columns of `offer_rows` (one entry per offer left with units, ordered by market, reservation price, seller name, tile name):
    market, seller, tile (interned ids), reservation, quantity, origin (the offer's place in its market's list of offers left)."""
from collections import namedtuple
from typing import Dict, List, Sequence

import numpy

BidRows = namedtuple("BidRows", ("market", "buyer", "floor", "flexible", "reference", "elasticity", "budget", "maximum", "table_agent"))
OfferRows = namedtuple("OfferRows", ("market", "seller", "tile", "reservation", "quantity", "origin"))


TableColumns = namedtuple("TableColumns", ("year_markets", "cells", "on_tables"))
TableColumns.__doc__ = """The markets of a pack as rows of the year's table (`goods_year_markets.YearMarkets`): `cells[i]` is market i's row, `on_tables[i]`
whether it was cleared on the order tables (its bids, offers left and settlement are then read from the table's columns, not from objects)."""


def table_columns(markets: dict, market_keys: Sequence):
    """`TableColumns` of the markets when they all share one filled year table, else None (a market made alone, a test's)."""
    sorted_cells = getattr(markets, "sorted_cells", None)       # `goods_left_markets.LeftMarkets`: the rows are known without making a market
    if sorted_cells is not None:
        shared = markets.year_markets
        if not len(markets) or not shared.first_round_filled or len(market_keys) != len(markets):
            return None
        cells = sorted_cells()
        return TableColumns(shared, cells, shared.table.way[cells] != 2)
    lefts = [markets[key] for key in market_keys]
    shared = lefts[0].year_markets if lefts else None
    if shared is None or not shared.first_round_filled or not all(each.year_markets is shared for each in lefts):
        return None
    cells = numpy.array([each.row for each in lefts], dtype=numpy.int64)
    return TableColumns(shared, cells, shared.table.way[cells] != 2)


def _ranges(first: numpy.ndarray, count: numpy.ndarray) -> numpy.ndarray:
    """The places `first[i] .. first[i] + count[i] - 1` for every i, one after another."""
    stops = numpy.cumsum(count)
    return numpy.repeat(first - (stops - count), count) + numpy.arange(int(stops[-1]) if len(stops) else 0, dtype=numpy.int64)


class Interner:
    """Distinct names numbered by first sight; `names[id]` is the name, `ids[name]` the id."""

    def __init__(self):
        self.names: List[str] = []
        self.ids: Dict[str, int] = {}

    def of(self, name: str) -> int:
        found = self.ids.get(name)
        if found is None:
            found = self.ids[name] = len(self.names)
            self.names.append(name)
        return found

    def of_numbers(self, numbers: numpy.ndarray, name_list: Sequence[str]) -> numpy.ndarray:
        """The id of the name each number has in `name_list`, for a whole column (each distinct number looked up once)."""
        if not len(numbers):
            return numpy.zeros(0, dtype=numpy.int64)
        distinct, inverse = numpy.unique(numbers, return_inverse=True)
        return numpy.array([self.of(name_list[each]) for each in distinct.tolist()], dtype=numpy.int64)[inverse]

    def ranks(self) -> numpy.ndarray:
        """Per id: its place when all the names are sorted as text (names are distinct, so no ties)."""
        order = sorted(range(len(self.names)), key=self.names.__getitem__)
        ranks = numpy.empty(len(self.names), dtype=numpy.int64)
        ranks[order] = numpy.arange(len(self.names), dtype=numpy.int64)
        return ranks


def _empty_bids() -> BidRows:
    return BidRows(numpy.zeros(0, dtype=numpy.int64), numpy.zeros(0, dtype=numpy.int64), *[numpy.zeros(0) for _each in range(6)],
                   numpy.zeros(0, dtype=numpy.int64))


def bid_rows(markets: dict, market_keys: Sequence, orders, agents: Interner, columns=None) -> BidRows:
    """The first-round bids of every market: a market on the tables from the order table's columns, one on the objects from its `Bid`s.
    `table_agent` is the buyer's book number for an entry of a market on the tables, else -1."""
    table = orders.tables()[0] if orders is not None else None
    names = orders.book.agent_ids.name_list if orders is not None else None
    pieces = []
    on_tables = [(index, markets[key].rows) for index, key in enumerate(market_keys) if markets[key].rows is not None] if columns is None else []
    if columns is not None and columns.on_tables.any():
        here = numpy.flatnonzero(columns.on_tables)
        cells = columns.cells[here]
        counts = columns.year_markets.table.bid_count[cells]
        rows = columns.year_markets.bid_rows()[_ranges(columns.year_markets.table.bid_first[cells], counts)]
        market = numpy.repeat(here, counts)
        number = table.buyer[rows]
        pieces.append(BidRows(market, agents.of_numbers(number, names), table.floor_quantity[rows], table.flexible_quantity[rows],
                              table.reference_price[rows], table.elasticity[rows], table.budget[rows], table.maximum_price[rows],
                              number.astype(numpy.int64)))
    if on_tables:
        rows = numpy.concatenate([each.bid_array for _index, each in on_tables])
        market = numpy.repeat(numpy.array([index for index, _each in on_tables], dtype=numpy.int64),
                              [len(each.bid_array) for _index, each in on_tables])
        number = table.buyer[rows]
        pieces.append(BidRows(market, agents.of_numbers(number, names), table.floor_quantity[rows], table.flexible_quantity[rows],
                              table.reference_price[rows], table.elasticity[rows], table.budget[rows], table.maximum_price[rows],
                              number.astype(numpy.int64)))
    objects = [(index, bid) for index, key in enumerate(market_keys) if (markets[key].rows is None if columns is None else not columns.on_tables[index])
               for bid in markets[key].bids]
    if objects:
        figures = numpy.array([(bid.floor_quantity, bid.flexible_quantity, bid.reference_price, bid.elasticity, bid.budget,
                                bid.maximum_price) for _index, bid in objects], dtype=numpy.float64).reshape(-1, 6)
        pieces.append(BidRows(numpy.array([index for index, _bid in objects], dtype=numpy.int64),
                              numpy.array([agents.of(bid.buyer) for _index, bid in objects], dtype=numpy.int64),
                              *[figures[:, column].copy() for column in range(6)], numpy.full(len(objects), -1, dtype=numpy.int64)))
    if not pieces:
        return _empty_bids()
    return BidRows(*[numpy.concatenate(each) for each in zip(*pieces)])


def bought_columns(markets: dict, market_keys: Sequence, rows: BidRows, agents: Interner, agent_count: int, columns=None) -> tuple:
    """(units received, money paid) in the first round's settlement for each bid entry (zero where the buyer is not in the market's
    `bought`). A market on the tables whose `bought` kept its columns is read with one search over all of them (`agent_count`: the book's agents,
    which numbers the rows' agents by); another is looked up by buyer name."""
    units = numpy.zeros(len(rows.market))
    money = numpy.zeros(len(rows.market))
    stride = agent_count + 1
    key_parts, unit_parts, money_parts = [], [], []
    by_name = []
    if columns is not None:
        cell, agent, given, paid = columns.year_markets.bought()
        index_of_cell = numpy.full(int(columns.year_markets.table.row_count[0]), -1, dtype=numpy.int64)
        index_of_cell[columns.cells] = numpy.arange(len(columns.cells), dtype=numpy.int64)
        if len(agent):
            key_parts.append(index_of_cell[cell] * stride + agent)
            unit_parts.append(given)
            money_parts.append(paid)
    for index, key in enumerate(market_keys):
        if columns is not None and columns.on_tables[index]:
            continue
        bought = markets[key].bought
        if columns is None and hasattr(bought, "columns") and markets[key].rows is not None:
            agent, given, paid = bought.columns()
            if len(agent):
                key_parts.append(index * stride + agent)
                unit_parts.append(given)
                money_parts.append(paid)
        elif bought:
            by_name.append(index)
    if key_parts and len(rows.market):
        keys = numpy.concatenate(key_parts)
        order = numpy.argsort(keys, kind="stable")
        keys, given, paid = keys[order], numpy.concatenate(unit_parts)[order], numpy.concatenate(money_parts)[order]
        ask = rows.market * stride + rows.table_agent
        place = numpy.searchsorted(keys, ask, side="right") - 1
        found = (rows.table_agent >= 0) & (place >= 0) & (keys[numpy.maximum(place, 0)] == ask)
        units[found], money[found] = given[place[found]], paid[place[found]]
    if by_name:
        for entry in numpy.flatnonzero(numpy.isin(rows.market, by_name)).tolist():
            found = markets[market_keys[rows.market[entry]]].bought.get(agents.names[rows.buyer[entry]])
            if found is not None:
                units[entry], money[entry] = found
    return units, money


def offer_rows(markets: dict, market_keys: Sequence, orders, agents: Interner, tiles: Interner, columns=None) -> OfferRows:
    """The offers left with units in every market, in clearing order within a market (cheapest reservation, then seller and tile name;
    equal offers keep the order of the market's list). A market on the tables reads the order table's units left."""
    table = orders.tables()[1] if orders is not None else None
    pieces = []
    on_tables = [(index, markets[key].rows) for index, key in enumerate(market_keys) if markets[key].rows is not None] if columns is None else []
    if columns is not None and columns.on_tables.any():
        here = numpy.flatnonzero(columns.on_tables)
        cells = columns.cells[here]
        counts = columns.year_markets.table.left_count[cells]
        places = _ranges(columns.year_markets.table.left_first[cells], counts)
        rows = columns.year_markets.left_rows()[places]
        pieces.append(OfferRows(numpy.repeat(here, counts), agents.of_numbers(table.seller[rows], orders.book.agent_ids.name_list),
                                tiles.of_numbers(table.tile[rows], orders.book.tile_ids.name_list), table.reservation_price[rows],
                                columns.year_markets.left_units()[places], numpy.arange(len(rows), dtype=numpy.int64) - numpy.repeat(numpy.cumsum(counts) - counts, counts)))
    if on_tables:
        rows = numpy.concatenate([each.left_array for _index, each in on_tables])
        counts = [len(each.left_array) for _index, each in on_tables]
        market = numpy.repeat(numpy.array([index for index, _each in on_tables], dtype=numpy.int64), counts)
        starts = numpy.repeat(numpy.cumsum([0, *counts[:-1]]), counts)
        pieces.append(OfferRows(market, agents.of_numbers(table.seller[rows], orders.book.agent_ids.name_list),
                                tiles.of_numbers(table.tile[rows], orders.book.tile_ids.name_list), table.reservation_price[rows],
                                table.quantity_left[rows], numpy.arange(len(rows), dtype=numpy.int64) - starts))
    objects = [(index, place, offer) for index, key in enumerate(market_keys) if (markets[key].rows is None if columns is None else not columns.on_tables[index])
               for place, offer in enumerate(markets[key].offers)]
    if objects:
        pieces.append(OfferRows(numpy.array([index for index, _place, _offer in objects], dtype=numpy.int64),
                                numpy.array([agents.of(offer.seller) for _index, _place, offer in objects], dtype=numpy.int64),
                                numpy.array([tiles.of(offer.tile) for _index, _place, offer in objects], dtype=numpy.int64),
                                numpy.array([offer.reservation_price for _index, _place, offer in objects], dtype=numpy.float64),
                                numpy.array([offer.quantity for _index, _place, offer in objects], dtype=numpy.float64),
                                numpy.array([place for _index, place, _offer in objects], dtype=numpy.int64)))
    if not pieces:
        return OfferRows(*[numpy.zeros(0, dtype=kind) for kind in (numpy.int64, numpy.int64, numpy.int64, float, float, numpy.int64)])
    joined = OfferRows(*[numpy.concatenate(each) for each in zip(*pieces)])
    keep = numpy.flatnonzero(joined.quantity > 0.0)
    kept = OfferRows(*[each[keep] for each in joined])
    order = numpy.lexsort((tiles.ranks()[kept.tile], agents.ranks()[kept.seller], kept.reservation, kept.market))
    return OfferRows(*[each[order] for each in kept])
