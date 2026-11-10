"""The quote figures of every market of a good that did not trade, in one kernel call: the token minimum price from the bids'
reference prices, then `goods_table_quotes.untraded_figures` and `wanted_by_market` over the good's rows grouped by market
(`goods_good_clear.Untraded` made the gathers and the three calls one after another)."""
import numpy

from sim.jit import njit

from .goods_table_quotes import untraded_figures, wanted_by_market
from .goods_table_scales import price_scales


@njit
def untraded_columns(bids, offers, bid_grouped, bid_ptr, offer_grouped, offer_ptr, last_price, minimum_share):
    """(lowest_ask, lowest_clamped, supply, funded, best_bid, wanted) per market of the good, whose bid rows are `bid_grouped` cut by
    `bid_ptr` and offer rows `offer_grouped` cut by `offer_ptr`; `last_price` is each market's remembered price (NaN: none).
    `wanted` is what the bids ask for at the lowest ask (else the best bid)."""
    reference = bids.reference_price[bid_grouped]
    scale = price_scales(bid_ptr, reference, last_price)
    has_minimum = ~numpy.isnan(scale)
    minimum = numpy.where(has_minimum, minimum_share * numpy.where(has_minimum, scale, 0.0), 0.0)
    budget, maximum = bids.budget[bid_grouped], bids.maximum_price[bid_grouped]
    lowest_ask, lowest_clamped, supply, funded, best_bid = untraded_figures(
        bid_ptr, offer_ptr, budget, maximum, offers.reservation_price[offer_grouped], offers.quantity[offer_grouped], minimum, has_minimum)
    asked = numpy.where(numpy.isnan(lowest_ask), best_bid, lowest_ask)
    wanted = wanted_by_market(bid_ptr, asked, bids.floor_quantity[bid_grouped], bids.flexible_quantity[bid_grouped], reference,
                              bids.elasticity[bid_grouped], budget, maximum)
    return lowest_ask, lowest_clamped, supply, funded, best_bid, wanted
