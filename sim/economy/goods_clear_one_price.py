"""The clearing rule for a good's markets: each market trades at one price, where its buyers' schedules meet its sellers'
offers at the reservation prices they posted (`goods_market.clear_at_one_price`). The sellers do not re-price, search for
an ask or raise one inside the year: the market finds the price, and what a seller will not let go at it stays in stock.
It stands where `goods_good_clear.clear_good` stands (rule_sets.py) and returns the same `GoodClearing`."""
import dataclasses
from typing import Sequence

from . import goods_market, stock_supply
from .goods_good_clear import GoodClearing, Untraded, note_household_limit
from .goods_table_group import note_stock_slots, rows_of_good
from .types import Fill, Pairing


def pairing_of(fills: Sequence[Fill]) -> Pairing:
    """Who bought from whom in a market that traded at one price, which the settlement posts pair by pair: the buyers'
    fills are matched to the sellers' in the fills' own order, each buyer taking from the next seller with units left.
    Every pair trades at the one price, so the matching moves no money between agents; it only says whose units went
    to whom."""
    buys = [fill for fill in fills if fill.side == "buy" and fill.quantity > 0.0]
    sells = [fill for fill in fills if fill.side == "sell" and fill.quantity > 0.0]
    buyer_index, seller_index, quantity = [], [], []
    seller, left = 0, sells[0].quantity if sells else 0.0
    for buyer, fill in enumerate(buys):
        wanted = fill.quantity
        while wanted > 0.0 and seller < len(sells):
            taken = min(wanted, left)
            if taken > 0.0:
                buyer_index.append(buyer)
                seller_index.append(seller)
                quantity.append(taken)
            wanted -= taken
            left -= taken
            if left <= 0.0:
                seller += 1
                left = sells[seller].quantity if seller < len(sells) else 0.0
    return Pairing(tuple((fill.agent, fill.tile) for fill in buys), tuple((fill.agent, fill.tile) for fill in sells),
                   tuple(fill.price for fill in sells), tuple(buyer_index), tuple(seller_index), tuple(quantity))


def at_one_price(context, good: str, area: str, last_price, bids: list, offers: list):
    """(the offers the market cleared: the producers' cut along their supply curves, the rest as posted; the market
    cleared at one price, with who bought from whom)."""
    offers = stock_supply.offers_by_stock_level(context.setup, context.record, context.view, good, offers)
    result = goods_market.clear_at_one_price(bids, offers, good, area, context.setup.currency_id, last_price)
    return offers, dataclasses.replace(result, pairing=pairing_of(result.fills)) if result.quantity > 0.0 else result


def clear_good_at_one_price(context, good: str, good_id: int) -> GoodClearing:
    """Clear the markets of `good` that have orders, in area order, each at one price; a market with nothing on offer
    keeps its quote from the tables as under the other rules."""
    note_household_limit(context, good, good_id)
    orders = context.orders
    rows, flags, flags_of = rows_of_good(orders, good_id, context.book.agent_table.is_edge, False)     # no market goes to the batch
    if not len(rows.markets):
        return GoodClearing.empty()
    bids, offers = orders.tables()
    note_stock_slots(offers, context.book, good_id, rows.offer_rows)
    last_price = orders.memory_tables.goods_table.price[rows.markets]
    untraded = Untraded(bids, offers, rows, last_price)
    return GoodClearing(context, good, rows, None, None, untraded, flags_of, last_price, flags, on_objects=at_one_price)
