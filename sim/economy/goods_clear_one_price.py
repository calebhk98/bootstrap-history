"""The clearing rule for a good's markets: each market trades at one price. The price is the one where its buyers'
schedules meet its sellers' supply (the producers' curves over the price, `stock_supply` and `fresh_supply`, and the
other sellers' offers at the reservations they posted), moved no further from last year's than a year allows
(`price_step.within_a_years_move`; a market's first price is held as near to what its producers expect); where that holds the price short of the clearing one, the long side goes short
(`goods_market.clear_at_price`). Where the buyers' wants step down at the most some bid pays (a mint's price for the coin
metal) from more than is on offer to less, the market clears at that price and the bids that end there take what the
buyers who would pay more leave. A market that trades nothing quotes what its sellers ask (`untraded_quote`). The sellers do not re-price, search for an ask or raise one inside the year, and what a
seller will not let go at the price stays in stock. It stands where `goods_good_clear.clear_good` stands (rule_sets.py)
and returns the same `GoodClearing`."""
import dataclasses
import math
from typing import Callable, Optional, Sequence

from . import goods_market, market_quote, price_step, stock_supply
from .goods_good_clear import GoodClearing, Untraded, note_household_limit
from .goods_table_group import note_stock_slots, rows_of_good
from .types import QUOTE_LOWEST_UNFILLED_ASK, Bid, Fill, Offer, Pairing, Quote


PRICE_SOLVE_STEPS = 60      # a numerical bound: halvings of the bracket the clearing price is searched in
LOWEST_SHARE_OF_BRACKET_TOP = 1e-9   # a numerical bound: the bracket goes no lower than this share of its top (a pile many times its
                                     # target puts the bottom at nothing, which has no logarithm)
BID_TOP_RESOLUTION = 1e-9            # a numerical bound: a bid that ends within this share under the price the search found ends at it


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


def clearing_price(buyers, curves, posted: Sequence[Offer]) -> Optional[float]:
    """The price at which the market would clear this year: where the buyers' schedule meets the supply of the curves
    and the posted offers; where the buyers want more than everything on offer even at the curves' highest price, the
    price at which their wants fall to it. None where the market has neither a price to hold nor one to find."""
    if curves:
        top = max(curve.highest_price for curve in curves)
        price = price_where_supply_meets(buyers.schedule.total_at, lambda at: supply_at(at, curves, posted),
                                         min(curve.lowest_price for curve in curves), top)
        if price < top:
            return price
        posted = list(posted) + [curve.offer_at(top) for curve in curves]
    return goods_market.crossing(buyers, goods_market.in_clearing_order(posted), with_wants=False)[0]


def bid_top_at(bids: Sequence[Bid], price: float) -> Optional[float]:
    """The most a funded bid pays (`maximum_price`) where that is `price` or a hair under it, the highest of them; None
    where no bid ends there. The buyers' wants step down at a bid's top, and the search for the clearing price stops a
    hair above such a step with the bid left out: the market clears at the top itself (`at_one_price`)."""
    tops = [bid.maximum_price for bid in bids if bid.budget > 0.0 and price * (1.0 - BID_TOP_RESOLUTION) <= bid.maximum_price <= price]
    return max(tops) if tops else None


def untraded_quote(bids: Sequence[Bid], curves, posted: Sequence[Offer]) -> Optional[Quote]:
    """What a market that traded nothing this year quotes: `market_quote.no_trade_quote` over what its sellers ask (each
    curve's `asking_price` for the units it holds, the posted offers as posted). Where buyers would have paid an ask and
    still got nothing (the year's price was held under it), the quote is the lowest ask, which is where the price
    heads; None where no seller holds a unit and no buyer names a top."""
    asks = [Offer(curve.offer.seller, curve.offer.good, curve.offer.area, curve.offer.tile, curve.offer.quantity, curve.asking_price)
            for curve in curves] + list(posted)
    quote = market_quote.no_trade_quote(bids, asks)
    lowest = market_quote.lowest_unfilled_ask(asks)
    return Quote(QUOTE_LOWEST_UNFILLED_ASK, lowest) if quote is None and lowest is not None else quote


def price_moved_from(last_price: Optional[float], curves, buyers) -> Optional[float]:
    """The price the year's move is measured from: last year's; in a market with none, the price its producers are
    content at (the mean over their curves, by the units each holds), else the price its buyers reckon the good at. None
    where the market has none of these, and the first price is then whatever clears it."""
    if last_price is not None and last_price > 0.0:
        return last_price
    held = math.fsum(curve.offer.quantity for curve in curves)
    if held > 0.0:
        return math.fsum(curve.content_price * curve.offer.quantity for curve in curves) / held
    return buyers.price_scale


def at_one_price(context, good: str, area: str, last_price, bids: list, offers: list):
    """(the offers the market traded: each producer's as the units its supply curve lets go at the year's price, the
    rest as posted; the market's result at that one price, with who bought from whom)."""
    buyers = goods_market.Buyers(bids, last_price)
    curves, posted = stock_supply.curves_and_posted(context.setup, context.record, context.view, good, offers)
    found = clearing_price(buyers, curves, posted)
    price = price_step.within_a_years_move(found, price_moved_from(last_price, curves, buyers))
    if price is None or not price > 0.0:
        return offers, goods_market.clear_at_one_price(bids, offers, good, area, context.setup.currency_id, last_price, buyers)
    top = bid_top_at(buyers.bids, price) if price == found else None      # a price the year's move holds is no step in the wants
    if top is not None:
        price = top
    offers = posted + [curve.offer_at(price) for curve in curves]
    result = goods_market.clear_at_price(bids, offers, good, area, context.setup.currency_id, price, last_price, buyers,
                                         at_a_bid_top=top is not None)
    if result.quantity > 0.0:
        return offers, dataclasses.replace(result, pairing=pairing_of(result.fills))
    return offers, dataclasses.replace(result, quote=untraded_quote(buyers.bids, curves, posted))


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
