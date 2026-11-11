"""The share of a market's price that stays after a producer's addition, one request at a time on `Bid` objects and the Python search:
what `expansion_price.share_after_addition` did before the shares of a year were priced in one kernel call."""
import math
from unittest import mock

from sim.economy import expansion_price, goods_market


def plain_share(bids, traded, added):
    """The share for one request on the market of `bids` (objects); the crossing's kernel entry is off, so the Python search answers."""
    if not bids or not traded > 0.0 or not added > 0.0:
        return 1.0
    with mock.patch.object(goods_market, "_kernel_price", lambda *rest: None):
        before = expansion_price.price_with_supply(bids, "g", "a", traded)
        if before is None or not before > 0.0:
            return 1.0
        after = expansion_price.price_with_supply(bids, "g", "a", traded + added)
    return max(0.0, min(1.0, after / before)) if after is not None and math.isfinite(after) else 1.0
