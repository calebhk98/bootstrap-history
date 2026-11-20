"""The clearing rule for a good's markets: each market trades at one price, where its buyers' schedules meet its sellers'
offers at the reservation prices they posted (`goods_market.clear_at_one_price`). The sellers do not re-price, search for
an ask or raise one inside the year: the market finds the price, and what a seller will not let go at it stays in stock.
It stands where `goods_good_clear.clear_good` stands (rule_sets.py) and returns the same `GoodClearing`."""
import dataclasses
import math
from typing import Callable, Sequence

from . import goods_market, stock_supply
from .goods_good_clear import GoodClearing, Untraded, note_household_limit
from .goods_table_group import note_stock_slots, rows_of_good
from .types import Fill, Offer, Pairing


PRICE_SOLVE_STEPS = 60      # a numerical bound: halvings of the bracket the clearing price is searched in
LOWEST_SHARE_OF_BRACKET_TOP = 1e-9   # a numerical bound: the bracket goes no lower than this share of its top (a pile many times its
                                     # target puts the bottom at nothing, which has no logarithm)


def supply_at(price: float, curves, posted: Sequence[Offer]) -> float:
    """Units on the market at a price: what each supply curve lets go at it, and the posted offers that take it."""
    return (math.fsum(curve.supply_at(price) for curve in curves)
            + math.fsum(offer.quantity for offer in posted if offer.reservation_price <= price))


def price_where_supply_meets(demand_at: Callable[[float], float], supply_at_price: Callable[[float], float],
                             lowest: float, highest: float) -> float:
    """The lowest price from `lowest` to `highest` at which the units supplied (rising in the price) cover the units
    wanted (falling in it); `highest` where they do not even there, `lowest` where they do already. Found by halving
    the bracket in the log of the price."""
    lowest = max(lowest, highest * LOWEST_SHARE_OF_BRACKET_TOP)
    if supply_at_price(lowest) >= demand_at(lowest):
        return lowest
    if supply_at_price(highest) < demand_at(highest):
        return highest
    low, high = math.log(lowest), math.log(highest)
    for _step in range(PRICE_SOLVE_STEPS):
        middle = (low + high) / 2.0
        if supply_at_price(math.exp(middle)) >= demand_at(math.exp(middle)):
            high = middle
        else:
            low = middle
    return math.exp(high)


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
    """(the offers the market cleared: each producer's as the units its supply curve lets go at the clearing price, the
    rest as posted; the market cleared at one price, with who bought from whom)."""
    buyers = goods_market.Buyers(bids, last_price)
    curves, posted = stock_supply.curves_and_posted(context.setup, context.record, context.view, good, offers)
    if curves:
        price = price_where_supply_meets(buyers.schedule.total_at, lambda at: supply_at(at, curves, posted),
                                         min(curve.lowest_price for curve in curves), max(curve.highest_price for curve in curves))
        offers = posted + [curve.offer_at(price) for curve in curves]
    result = goods_market.clear_at_one_price(bids, offers, good, area, context.setup.currency_id, last_price, buyers)
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
