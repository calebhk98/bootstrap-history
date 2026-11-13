"""A merchant's year of orders and its credit request, over the packed markets of `merchants_book`.

The same rules as the per-good route search and the per-route commitments they replace (`merchants.candidate_routes`,
`merchants_shares.room_left`): the candidate rows come from one kernel over every good, and the bids and the
borrowing are sized by kernels that walk the rows best first, each commit changing the room the next row sees.
"""
import math
from typing import Dict, List, Mapping, Optional, Tuple

import numpy as np

from . import merchants, merchants_batch, merchants_book, merchants_book_kernel, merchants_legs
from .merchants_shares import MERCHANT_GROUP_SHARE, MERCHANT_SOURCE_SHARE, RouteShares
from .protocols import AgentOrders
from .types import Bid, GoodId, TileId


class _Stock:
    """What a merchant holds and expects, in the book's slots."""

    def __init__(self, route, merchant, held_stock, area_map):
        book = route.book
        self.held = np.zeros(book.slots, np.float64)
        self.slot_of_stock: Dict[Tuple[GoodId, TileId], int] = {}
        self.tiles_in_slot: Dict[int, List[Tuple[TileId, float]]] = {}     # the held (tile, quantity) of each slot's area, tiles sorted
        for (good, tile), quantity in held_stock.items():
            slot = route.slot_of_stock(area_map, good, tile)
            if slot is not None:
                self.slot_of_stock[(good, tile)] = slot
                self.held[slot] += quantity
                self.tiles_in_slot.setdefault(slot, []).append((tile, quantity))
        for tiles in self.tiles_in_slot.values():
            tiles.sort()
        for each in merchant.in_transit:
            slot = route.slot_of_stock(area_map, each.good, each.destination_tile)
            if slot is not None:
                self.held[slot] += each.quantity
        self.volumes = merchants_book.merchant_array(book, merchant.expected_volumes)
        self.expected = merchants_book.merchant_array(book, merchant.expected_prices)

    def expectation_of(self, good: GoodId, tile: TileId) -> Optional[float]:
        """The merchant's own expected price of the market a stock on `tile` sells in (None for none), from the slot array;
        `merchants.NOT_AT_HAND` for a stock that holds no slot."""
        slot = self.slot_of_stock.get((good, tile))
        if slot is None:
            return merchants.NOT_AT_HAND
        found = float(self.expected[slot])
        return None if math.isnan(found) else found


def _rows(route, merchant, stock, interest_rate, only_held=None, area_map=None) -> merchants_book.MerchantRows:
    """The candidate rows; with `only_held` ({good: [(tile, quantity)]}) those of the goods held, from the source
    areas holding them."""
    book = route.book
    good_allowed = source_allowed = None
    if only_held is not None:
        good_allowed = np.zeros(len(book.goods), np.bool_)
        source_allowed = np.zeros(book.slots, np.bool_)
        for good, held in only_held.items():
            index = book.index_of.get(good)
            if index is None:
                continue
            good_allowed[index] = True
            for tile, _quantity in held:
                slot = stock.slot_of_stock.get((good, tile))
                if slot is not None:
                    source_allowed[slot] = True
    if only_held is None:
        prepared = merchants_batch.rows_for(route, merchant.agent_id, float(interest_rate), merchant.home_tile, stock.expected,
                                         merchant.traded_tiles)
        if prepared is not None:
            return prepared
    return merchants_book.search(route, stock.expected, merchant.home_tile, interest_rate, merchants.MERCHANT_MARGIN_SHARE,
                                 good_allowed, source_allowed, merchant.traded_tiles)


def prepare_rows(route, merchants, interest_rate: float) -> None:
    """Search the candidate rows of these merchants in one call, for their `orders` or `credit_wanted` that follow on this `route`."""
    if merchants:
        merchants_batch.prepare(route, merchants, interest_rate, merchants_margin())


def merchants_margin() -> float:
    return merchants.MERCHANT_MARGIN_SHARE


def candidate_rows(merchant, view, carriage, area_map, held_stock, specs, interest_rate, only_held=None, route=None):
    """The rows of `merchants.candidate_routes` ((rank, good, source area, destination area, price here, outlay, most
    it pays), best first) from the packed search."""
    route = route or merchants_book.route_pass(view, carriage, area_map, specs)
    stock = _Stock(route, merchant, held_stock, area_map)
    rows = _rows(route, merchant, stock, interest_rate, only_held)
    book = route.book
    return [(rank, book.goods[good], book.areas[good][source], book.areas[good][destination], price_here, outlay, ceiling)
            for rank, good, source, destination, price_here, outlay, ceiling in zip(
                rows.rank.tolist(), rows.good.tolist(), rows.source.tolist(), rows.destination.tolist(),
                rows.price_here.tolist(), rows.outlay.tolist(), rows.ceiling.tolist())]


def _group_arrays(book, shares) -> Tuple[np.ndarray, np.ndarray, bool]:
    """(into, out of, whether the arrays are the shares themselves) of the commitments rivals have made."""
    if isinstance(shares, merchants_book.DenseShares):
        return shares.into, shares.out_of, True
    into, out_of = np.zeros(book.slots, np.float64), np.zeros(book.slots, np.float64)
    for table, array in ((shares.into, into), (shares.out_of, out_of)):
        for key, value in table.items():
            slot = book.slot_of.get(key)
            if slot is not None:
                array[slot] = value
    return into, out_of, False


def orders(merchant, view, carriage, area_map, cash: float, held_stock: Mapping[Tuple[GoodId, TileId], float], specs,
           interest_rate: float, shares=None, route=None, rows_out=None) -> AgentOrders:
    """The merchant's offers and bids for the year (`merchants.orders`). `shares` is what rival merchants have already
    committed this year (`RouteShares`, or `merchants_book.DenseShares` when the caller sizes many merchants over one
    `route` pass); this merchant adds its own to it. With `rows_out` (an `OrderRows`) the bids and offers are written to it as rows,
    offers first as `OrderRows` takes them in any order, and no `Bid` or `Offer` is made; the answer then holds no orders."""
    route = route or merchants_book.route_pass(view, carriage, area_map, specs)
    book = route.book
    shares = shares if shares is not None else RouteShares()
    group_into, group_out, dense = _group_arrays(book, shares)
    merchant.routes = {}
    held_index = merchants.held_by_good(held_stock)
    stock = _Stock(route, merchant, held_stock, area_map)
    remaining = max(0.0, cash) * (1.0 - merchants.BUDGET_SAFETY_SHARE)     # a hair kept back: borrowed cash is all spent
    rows = _rows(route, merchant, stock, interest_rate, None if remaining > 0.0 else held_index)
    shares_args = (merchants.MERCHANT_MARKET_SHARE, MERCHANT_GROUP_SHARE, MERCHANT_SOURCE_SHARE)
    # stock already held where a route out pays is carried along every paying route, by what each destination takes
    held_rooms: Dict[Tuple[GoodId, TileId], Dict[Tuple[TileId, str], float]] = {}
    held_best: Dict[Tuple[GoodId, TileId], Tuple[TileId, str]] = {}     # candidates run best first
    if stock.tiles_in_slot:
        holding_source = np.zeros(book.slots, np.bool_)
        holding_source[list(stock.tiles_in_slot)] = True
        held_rows = np.flatnonzero(holding_source[rows.source_slot])
        room_of_row = merchants_book_kernel.rooms_of(
            rows.destination_slot[held_rows], rows.source_slot[held_rows], stock.volumes, stock.held, book.zeros, group_into,
            group_out, *shares_args).tolist()
        for row, room in zip(held_rows.tolist(), room_of_row):
            good_index = int(rows.good[row])
            good = book.goods[good_index]
            destination = book.areas[good_index][int(rows.destination[row])]
            for tile, quantity in stock.tiles_in_slot.get(int(rows.source_slot[row]), ()):
                if quantity > 0.0 and tile != destination.anchor_tile:
                    leg = (destination.anchor_tile, destination.area_id)
                    held_best.setdefault((good, tile), leg)
                    held_rooms.setdefault((good, tile), {})[leg] = room
    for key, rooms in held_rooms.items():
        weights = merchants_legs.held_weights(rooms) or {held_best[key]: 1.0}     # stock with nowhere to go still follows the best route
        merchant.routes[key] = merchants_legs.from_weights(weights)
    if rows_out is None:
        offers = [offer for offer in merchants._holding_offers(merchant, view, area_map, held_stock, specs, interest_rate)
                  if (offer.good, offer.tile) not in merchant.routes]
    else:
        for good, area, tile, quantity, reservation in merchants.holding_offer_figures(merchant, view, area_map, held_stock, specs, interest_rate,
                                                                                       stock.expectation_of):
            if (good, tile) not in merchant.routes:
                rows_out.offer(merchant.agent_id, good, area, tile, quantity, reservation)
        offers = []
    bids: List[Bid] = []
    bought: Dict[Tuple[GoodId, TileId], Dict[Tuple[TileId, str], float]] = {}
    if remaining > 0.0:
        quantities = merchants_book_kernel.commit_orders(
            rows.destination_slot, rows.source_slot, rows.outlay, remaining, stock.volumes, stock.held,
            np.zeros(book.slots, np.float64), group_into, group_out, *shares_args)
        for row in np.flatnonzero(quantities > 0.0).tolist():
            good_index = int(rows.good[row])
            good = book.goods[good_index]
            source = book.areas[good_index][int(rows.source[row])]
            destination = book.areas[good_index][int(rows.destination[row])]
            quantity = float(quantities[row])
            if not dense:
                shares.commit(good, source.area_id, destination.area_id, quantity)
            price_here = float(rows.price_here[row])
            leg = (destination.anchor_tile, destination.area_id)
            by_leg = bought.setdefault((good, source.anchor_tile), {})
            by_leg[leg] = by_leg.get(leg, 0.0) + quantity
            if rows_out is None:
                bids.append(Bid(merchant.agent_id, good, source.area_id, source.anchor_tile, 0.0, quantity,
                                price_here, merchants.MERCHANT_BID_ELASTICITY, quantity * price_here,
                                maximum_price=float(rows.ceiling[row])))
            else:
                rows_out.bid(merchant.agent_id, good, source.area_id, source.anchor_tile, 0.0, quantity, price_here,
                             merchants.MERCHANT_BID_ELASTICITY, quantity * price_here, maximum_price=float(rows.ceiling[row]))
    for key, by_leg in bought.items():      # what was bought is carried to the destinations it was bought for
        merchant.routes[key] = merchants_legs.from_weights(by_leg)
    return AgentOrders(bids=tuple(bids), offers=tuple(offers))


def credit_wanted(merchant, view, carriage, area_map, cash: float, held_stock, specs, interest_rate: float,
                  limit: float, route=None) -> Tuple[float, float]:
    """(loan wanted, gain it is expected to earn) for the cargo `cash` cannot buy, within `limit`
    (`merchants_credit.credit_request`)."""
    route = route or merchants_book.route_pass(view, carriage, area_map, specs)
    book = route.book
    stock = _Stock(route, merchant, held_stock, area_map)
    rows = _rows(route, merchant, stock, interest_rate)
    wanted, gain = merchants_book_kernel.commit_credit(
        rows.destination_slot, rows.source_slot, rows.rank, rows.outlay, cash, limit, stock.volumes, stock.held,
        np.zeros(book.slots, np.float64), np.zeros(book.slots, np.float64), np.zeros(book.slots, np.float64),
        merchants.MERCHANT_MARKET_SHARE, MERCHANT_GROUP_SHARE, MERCHANT_SOURCE_SHARE)
    return float(wanted), float(gain)
