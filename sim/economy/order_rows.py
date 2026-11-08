"""The one door a source of goods orders writes through: rows for the book of orders (`goods_order_book.GoodsOrderBook`), no `Bid` or
`Offer` object made on the way.

A source (the mint, the state, a merchant, a firm bidding for ground or plant, an engine seat) adds one order at a time by name and
figure (`OrderRows.bid`, `OrderRows.offer`) and calls `write` once; the names become the book's ids in one pass (an unseen name is
admitted, the names new to one `write` in sorted order, as the book's own flush does) and the rows are appended in the order they
were added. Into a `GoodsOrderBook` the rows wait by name in their place in the arrival order, so the names of everything waiting are
numbered together at the next flush, as when each order waited as an object.
A source that computes in arrays has the book's `append_bids`/`append_offers` and its own kernel instead.

`bids_from` and `offers_from` take the objects of a rule that still makes them (`households_store.store_bids`, a seat's own bids) and
unpack them into the same rows, so the book receives no object either way. When the book is a plain `{(good, area): (bids, offers)}`
dict (a test), `write` builds the objects and appends them as the legacy door did."""
import math
from typing import Iterable, List

from .goods_order_book import GoodsOrderBook
from .goods_order_objects import make_bid, make_offer
from .goods_order_tables import OTHER


class NamedBids:
    """The bids of one `OrderRows.write`, as an item a `GoodsOrderBook` numbers and writes at its next flush."""

    def __init__(self, buyer, good, area, tile, priority, figures, source: int):
        self.buyer, self.good, self.area, self.tile, self.priority, self.figures, self.source = buyer, good, area, tile, priority, figures, source

    def names(self) -> tuple:
        return self.buyer, self.good, self.tile, list(dict.fromkeys(zip(self.good, self.area)))

    def rows(self, book: GoodsOrderBook) -> tuple:
        return (book.agent_ids_of(self.buyer), book.good_ids_of(self.good), book.tile_ids_of(self.tile),
                book.market_ids(self.good, self.area), self.priority, self.figures)


class NamedOffers:
    """The offers of one `OrderRows.write`, as an item a `GoodsOrderBook` numbers and writes at its next flush."""

    def __init__(self, seller, good, area, tile, quantity, reservation, source: int):
        self.seller, self.good, self.area, self.tile, self.quantity, self.reservation, self.source = (
            seller, good, area, tile, quantity, reservation, source)

    def names(self) -> tuple:
        return self.seller, self.good, self.tile, list(dict.fromkeys(zip(self.good, self.area)))

    def rows(self, book: GoodsOrderBook) -> tuple:
        return (book.agent_ids_of(self.seller), book.good_ids_of(self.good), book.tile_ids_of(self.tile),
                book.market_ids(self.good, self.area), self.quantity, self.reservation)


class OrderRows:
    """The bids and offers one source has added, by name, until `write` appends them to a book of orders."""

    def __init__(self, order_book, source: int = OTHER):
        self.order_book, self.source = order_book, source
        self._clear()

    def _clear(self) -> None:
        self.buyer: List[str] = []
        self.bid_good: List[str] = []
        self.bid_area: List[str] = []
        self.bid_tile: List[str] = []
        self.priority: List[int] = []
        self.figures: List[tuple] = []        # per bid: floor, flexible, reference price, elasticity, budget, maximum price
        self.seller: List[str] = []
        self.offer_good: List[str] = []
        self.offer_area: List[str] = []
        self.offer_tile: List[str] = []
        self.quantity: List[float] = []
        self.reservation: List[float] = []

    def bid(self, buyer: str, good: str, area: str, tile: str, floor_quantity: float, flexible_quantity: float, reference_price: float,
            elasticity: float, budget: float, priority: int = 0, maximum_price: float = math.inf) -> None:
        """One bid (the fields of `types.Bid`, in its order)."""
        self.buyer.append(buyer)
        self.bid_good.append(good)
        self.bid_area.append(area)
        self.bid_tile.append(tile)
        self.priority.append(priority)
        self.figures.append((floor_quantity, flexible_quantity, reference_price, elasticity, budget, maximum_price))

    def offer(self, seller: str, good: str, area: str, tile: str, quantity: float, reservation_price: float) -> None:
        """One offer (the fields of `types.Offer`, in its order)."""
        self.seller.append(seller)
        self.offer_good.append(good)
        self.offer_area.append(area)
        self.offer_tile.append(tile)
        self.quantity.append(quantity)
        self.reservation.append(reservation_price)

    def bids_from(self, bids: Iterable) -> None:
        """The bids a rule still makes as objects, added as rows."""
        for bid in bids:
            self.bid(bid.buyer, bid.good, bid.area, bid.tile, bid.floor_quantity, bid.flexible_quantity, bid.reference_price,
                     bid.elasticity, bid.budget, bid.priority, bid.maximum_price)

    def offers_from(self, offers: Iterable) -> None:
        """The offers a rule still makes as objects, added as rows."""
        for offer in offers:
            self.offer(offer.seller, offer.good, offer.area, offer.tile, offer.quantity, offer.reservation_price)

    def write(self) -> None:
        """Hand what was added to the book of orders (bids, then offers, each in the order added) and start empty again."""
        target = self.order_book
        if isinstance(target, GoodsOrderBook):
            self._wait_in(target)
        else:
            self._write_objects(target)
        self._clear()

    def _wait_in(self, orders) -> None:
        """Hand the names and figures to the `GoodsOrderBook`, which numbers them with everything else waiting at its next flush."""
        if self.buyer:
            orders.add_named_bids(NamedBids(self.buyer, self.bid_good, self.bid_area, self.bid_tile, self.priority, self.figures, self.source))
        if self.seller:
            orders.add_named_offers(NamedOffers(self.seller, self.offer_good, self.offer_area, self.offer_tile, self.quantity, self.reservation,
                                                self.source))

    def _write_objects(self, target) -> None:
        for position, buyer in enumerate(self.buyer):
            bid = make_bid(buyer, self.bid_good[position], self.bid_area[position], self.bid_tile[position], *self.figures[position][:5],
                           self.priority[position], self.figures[position][5])
            target.setdefault((bid.good, bid.area), ([], []))[0].append(bid)
        for position, seller in enumerate(self.seller):
            offer = make_offer(seller, self.offer_good[position], self.offer_area[position], self.offer_tile[position],
                               self.quantity[position], self.reservation[position])
            target.setdefault((offer.good, offer.area), ([], []))[1].append(offer)
