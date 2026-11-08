"""A traded market's clearing as the tables hold it: an `ArrayClearing` whose readers use the order tables' columns, not the
`Bid` and `Offer` objects of its rows.

The allocation arrays are the batch's (`goods_year_results.final_allocations`); the bid and offer rows of the market are the
batch pack's. `fills` and `pairing` are built on first read, as `ArrayClearing`'s are; the questions the year ledger, the mint
and the respend ask (`bought_by`, `taken_by`, `sold_by_key`, `offers_left`, `sold_by_producers`) are answered from columns."""
from typing import List

import numpy

from .goods_market_fills import make_fill
from .goods_year_results import ArrayClearing
from .types import Offer, Pairing


class TableClearing(ArrayClearing):
    """A clearing that traded, read from the tables of a `TableBatch`."""

    def _slices(self):
        """(bid rows, offer rows) of the market, in clearing order and in seller-and-tile order, and the arrays' first places."""
        batch, market = self.batch, self.market
        first_bid, last_bid = batch.bid_ptr[market], batch.bid_ptr[market + 1]
        first_offer, last_offer = batch.offer_ptr[market], batch.offer_ptr[market + 1]
        return (batch.pack.bid_rows[first_bid:last_bid], batch.pack.offer_rows[first_offer:last_offer], first_bid, first_offer)

    def _names(self):
        book = self.batch.orders.book
        return book.agent_ids.name_list, book.tile_ids.name_list

    @property
    def fills(self):
        cached = self.__dict__.get("_fills")
        if cached is None:
            batch = self.batch
            bid_rows, offer_rows, first_bid, first_offer = self._slices()
            bids, offers = batch.orders.tables()
            agents, tiles = self._names()
            quantity = batch.bid_quantity[first_bid:first_bid + len(bid_rows)]
            cost = batch.bid_cost[first_bid:first_bid + len(bid_rows)]
            fills = [make_fill(agents[buyer], self.good, self.area, tiles[tile], float(units), float(paid / units), "buy")
                     for buyer, tile, units, paid in zip(bids.buyer[bid_rows].tolist(), bids.tile[bid_rows].tolist(),
                                                         quantity.tolist(), cost.tolist()) if units > 0.0]
            sold = batch.sold[first_offer:first_offer + len(offer_rows)]
            ask = batch.ask[first_offer:first_offer + len(offer_rows)]
            for place in numpy.argsort(batch.rank[first_offer:first_offer + len(offer_rows)], kind="stable").tolist():
                if sold[place] > 0.0:
                    row = offer_rows[place]
                    fills.append(make_fill(agents[offers.seller[row]], self.good, self.area, tiles[offers.tile[row]],
                                           float(sold[place]), float(ask[place]), "sell"))
            cached = self.__dict__["_fills"] = tuple(fills)
        return cached

    @property
    def pairing(self) -> Pairing:
        cached = self.__dict__.get("_pairing")
        if cached is None:
            batch, market = self.batch, self.market
            bid_rows, offer_rows, first_bid, first_offer = self._slices()
            bids, offers = batch.orders.tables()
            agents, tiles = self._names()
            order = numpy.argsort(batch.rank[first_offer:first_offer + len(offer_rows)], kind="stable")
            place_of = numpy.empty(len(order), dtype=numpy.int64)
            place_of[order] = numpy.arange(len(order))
            ranked = offer_rows[order]
            pairs = slice(batch.pair_ptr[market], batch.pair_ptr[market + 1])
            cached = self.__dict__["_pairing"] = Pairing(
                tuple(zip(map(agents.__getitem__, bids.buyer[bid_rows].tolist()), map(tiles.__getitem__, bids.tile[bid_rows].tolist()))),
                tuple(zip(map(agents.__getitem__, offers.seller[ranked].tolist()), map(tiles.__getitem__, offers.tile[ranked].tolist()))),
                tuple(batch.ask[first_offer + order].tolist()),
                tuple((batch.pair_bid[pairs] - first_bid).tolist()),
                tuple(place_of[batch.pair_offer[pairs] - first_offer].tolist()),
                tuple(batch.pair_quantity[pairs].tolist()))
        return cached

    def sold_by_key(self) -> dict:
        batch = self.batch
        _bid_rows, offer_rows, _first_bid, first_offer = self._slices()
        _bids, offers = batch.orders.tables()
        agents, tiles = self._names()
        sold: dict = {}
        units = batch.sold[first_offer:first_offer + len(offer_rows)]
        for seller, tile, quantity in zip(offers.seller[offer_rows].tolist(), offers.tile[offer_rows].tolist(), units.tolist()):
            if quantity > 0.0:
                key = (agents[seller], tiles[tile])
                sold[key] = sold.get(key, 0.0) + float(quantity)
        return sold

    def offers_left(self) -> List[Offer]:
        batch = self.batch
        _bid_rows, offer_rows, _first_bid, first_offer = self._slices()
        remaining = batch.left[first_offer:first_offer + len(offer_rows)]
        kept = numpy.flatnonzero(remaining > 0.0)
        return batch.orders.offers_of(offer_rows[kept], remaining[kept])

    def bought_by(self, watchers) -> dict:
        batch = self.batch
        bid_rows, _offer_rows, first_bid, _first_offer = self._slices()
        bids, _offers = batch.orders.tables()
        agents, tiles = self._names()
        numbers = batch.orders.book.agent_ids.numbers
        ids = [numbers[name] for name in watchers if name in numbers]
        found: dict = {}
        if not ids:
            return found
        quantity = batch.bid_quantity[first_bid:first_bid + len(bid_rows)]
        for place in numpy.flatnonzero(numpy.isin(bids.buyer[bid_rows], ids) & (quantity > 0.0)).tolist():
            row = bid_rows[place]
            buyer = agents[bids.buyer[row]]
            found.setdefault(buyer, []).append(make_fill(
                buyer, self.good, self.area, tiles[bids.tile[row]], float(quantity[place]),
                float(batch.bid_cost[first_bid + place] / quantity[place]), "buy"))
        return found

    def taken_by(self, buyer: str) -> List[tuple]:
        batch, market = self.batch, self.market
        bid_rows, offer_rows, first_bid, first_offer = self._slices()
        bids, offers = batch.orders.tables()
        agents, tiles = self._names()
        number = batch.orders.book.agent_ids.numbers.get(buyer)
        pairs = slice(batch.pair_ptr[market], batch.pair_ptr[market + 1])
        found = []
        if number is None:
            return found
        for bid_at, offer_at, quantity in zip((batch.pair_bid[pairs] - first_bid).tolist(), (batch.pair_offer[pairs] - first_offer).tolist(),
                                              batch.pair_quantity[pairs].tolist()):
            if bids.buyer[bid_rows[bid_at]] == number:
                row = offer_rows[offer_at]
                found.append((agents[offers.seller[row]], tiles[offers.tile[row]], quantity, float(batch.ask[first_offer + offer_at])))
        return found

    def sold_by_producers(self) -> float:
        batch = self.batch
        _bid_rows, offer_rows, _first_bid, first_offer = self._slices()
        _bids, offers = batch.orders.tables()
        sold = batch.sold[first_offer:first_offer + len(offer_rows)]
        edge = batch.orders.book.agent_table.is_edge[offers.seller[offer_rows]] != 0
        return float(sum(sold[(sold > 0.0) & ~edge].tolist()))
