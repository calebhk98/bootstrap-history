"""The price scale of each market of a good: what the token minimum price is a share of."""
import numpy

from sim.jit import njit


@njit
def price_scales(bid_ptr, reference_price, last_price):
    """Per market, the mean positive reference price of its bids, else its last price when positive, else NaN
    (`goods_market._price_scale`). The reference prices are added left to right."""
    markets = len(bid_ptr) - 1
    scale = numpy.full(markets, numpy.nan)
    for market in range(markets):
        total = 0.0
        count = 0
        for bid in range(bid_ptr[market], bid_ptr[market + 1]):
            if reference_price[bid] > 0.0:
                total += reference_price[bid]
                count += 1
        if count > 0:
            scale[market] = total / count
        elif last_price[market] > 0.0:
            scale[market] = last_price[market]
    return scale
