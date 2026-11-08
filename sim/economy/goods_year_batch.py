"""A good's markets re-priced, searched and cleared together, for a caller that holds its markets as lists of `Bid` and `Offer`
(the tests): `clear_markets` writes the lists into a book of orders and clears it with the table kernels the year uses
(goods_good_clear.py), and returns each market's offers after the sellers' re-pricing and the searches, and its clearing. The rules
are those of seller_offers.strategic_offers and unsold_search.clear_with_search, which still serve the markets the batch leaves out.

`batchable` is the rule that sends a market to the batch, stated over objects; `goods_table_group.batch_flags` applies it to columns.
A market is batched when it has units on offer, no book edge sells in it (the mint's wash of its own trades) and its good is
portable (ground has a rent to hold for, read off the land record)."""
from typing import List, Sequence, Tuple

from . import goods_good_clear, goods_order_book
from .goods_table_context import ClearingContext
from .types import Offer, is_edge


def batchable(setup, bids: Sequence, offers: Sequence[Offer], good: str, arrays) -> bool:
    if good not in arrays.matrices.goods.row:
        return False
    spec = setup.specs.get(good)
    if spec is not None and not spec.portable:
        return False
    units = False
    for offer in offers:
        if offer.quantity > 0.0:
            units = True
            if is_edge(offer.seller):
                return False
    return units


def clear_markets(setup, record, view, arrays, costs, markets: Sequence[tuple]) -> List[Tuple[List[Offer], object]]:
    """For each market (good, area, bids, offers, last price): (the offers after the sellers' re-pricing and the searches,
    the market's clearing with them). The last price is the remembered one the market's memory holds."""
    orders = goods_order_book.new_order_book(setup, record)
    for _good, _area, bids, offers, _last_price in markets:
        for bid in bids:
            orders.add_bid(bid)
        for offer in offers:
            orders.add_offer(offer)
    context = ClearingContext(setup, record, view, orders, arrays, costs)
    found = {}
    for good in sorted({market[0] for market in markets}):
        for each in goods_good_clear.clear_good(context, good, record.book.good_number(good)):
            found[(good, each.area)] = (list(each.objects()[1]), each.result)
    return [found[(good, area)] for good, area, _bids, _offers, _last_price in markets]
