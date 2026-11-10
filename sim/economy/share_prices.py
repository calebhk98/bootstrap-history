"""The shares of the price that stay after producers' additions, for a year's requests at once (`share_price_kernel`).

`shares_after_additions(markets' columns, orders, traded, request_market, request_added)` joins the markets' bids into one set of
columns and prices every request in one kernel call. The requests marked `needs_objects` are the ones the columns cannot answer; the
caller prices those on `Bid` objects (`expansion_price`)."""
from typing import Sequence, Tuple

import numpy

from .bid_columns import BidColumns
from . import goods_market
from .share_price_kernel import shares_after_additions as kernel


def _joined(pieces: Sequence[numpy.ndarray], dtype) -> numpy.ndarray:
    return numpy.concatenate(pieces).astype(dtype, copy=False) if len(pieces) else numpy.zeros(0, dtype=dtype)


def shares_after_additions(columns: Sequence[BidColumns], orders: Sequence[numpy.ndarray], traded: Sequence[float],
                           request_market: Sequence[int], request_added: Sequence[float]) -> Tuple[numpy.ndarray, numpy.ndarray]:
    """(share, needs_objects) for each request: market `request_market[request]` (an index into `columns`; requests in market order)
    gaining `request_added[request]` units a year over the `traded[market]` units the year cleared."""
    count = len(columns)
    market_start = numpy.zeros(count + 1, dtype=numpy.int64)
    market_start[1:] = numpy.cumsum([len(each) for each in orders], dtype=numpy.int64)
    request_start = numpy.zeros(count + 1, dtype=numpy.int64)
    request_start[1:] = numpy.cumsum(numpy.bincount(numpy.asarray(request_market, dtype=numpy.int64), minlength=count), dtype=numpy.int64)
    share = numpy.ones(len(request_market))
    needs_objects = numpy.zeros(len(request_market), dtype=numpy.bool_)
    kernel(*(_joined([each[field] for each in columns], numpy.float64) for field in range(6)), _joined(orders, numpy.int64),
           market_start, numpy.asarray(traded, dtype=numpy.float64), request_start, numpy.asarray(request_added, dtype=numpy.float64),
           goods_market.MINIMUM_PRICE_SHARE_OF_REFERENCE, share, needs_objects)
    return share, needs_objects
