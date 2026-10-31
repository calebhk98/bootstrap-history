"""How a market's buyers are sent to its sellers: each buyer splits its demand over the sellers by the logit on their asks,
every seller sells at its own ask, and what a sold-out seller could not serve is sent again to the sellers still holding stock.

Follows Eurace@Unibi, Cons_Goods/Household_Consumer_Functions.c, Household_rank_and_buy_goods_1 and _2, and
Cons_Goods/Mall_functions.c, Mall_update_mall_stocks_sales_rationing_1 and _2:
  * round 1: a household weighs the sellers that have stock by exp(-intensity * log ask) and sends its weekly budget
    to one drawn by those weights (here its demand is split over all of them by the weights, the expectation of the
    draw: price_setting.choice_shares, the function sellers plan with);
  * a seller whose requests exceed its stock serves each by stock / requests (here lower priority tiers first, then
    pro rata, as goods_market_ration.ration does);
  * round 2: a household that was rationed does the same among the sellers still holding stock, with the budget it has
    left, and is rationed again if need be; there is no third round, so what is left is unmet.
Eurace's households have one budget and no price-sensitive quantity; here a buyer's quantity at an ask is its schedule's
(Bid, goods_market.quantity_at), so a request is the buyer's quantity at that ask times its share, and in round 2 it is
the quantity unmet, limited by the money unspent and by what the schedule still wants at the new ask. A buyer does not
choose a seller asking above its maximum price (Eurace has no such ceiling; the seller would only be sent buyers who
cannot take it).
"""
from itertools import groupby
from typing import List, Sequence, Tuple

import numpy

from sim.book import ROUNDING_SHARE

from .goods_market_demand import DemandSchedule
from .price_setting import LOGIT_INTENSITY
from .types import Bid, Offer


class Allocation:
    """What the logit choice gave: per bid, the quantity bought and what it cost at the asks; per offer, the quantity
    sold; the round-1 requests in all (what buyers asked for at the asks before any seller ran out)."""

    def __init__(self, quantity: List[float], cost: List[float], sold: List[float], requested: float):
        self.quantity = quantity
        self.cost = cost
        self.sold = sold
        self.requested = requested


def _weights(asks: numpy.ndarray, stocked: numpy.ndarray, ceilings: numpy.ndarray) -> Tuple[numpy.ndarray, numpy.ndarray]:
    """(each offer's choice weight, each bid's sum of weights over the offers it may choose). A bid chooses among the
    offers in stock asking at or below its ceiling; the cheapest of those is the cheapest in stock whenever there is
    one, so weights are shared (price_setting.choice_weight, relative to that ask) and a bid's sum is the running total
    of the weights up to its ceiling, which `asks` (ascending) makes a prefix. The sum is 1 for a bid with no choice."""
    weights = numpy.zeros(len(asks))
    if stocked.any():
        cheapest = asks[numpy.argmax(stocked)]
        weights[stocked] = numpy.exp(-LOGIT_INTENSITY * numpy.log(asks[stocked] / cheapest))
    running = numpy.concatenate(([0.0], numpy.cumsum(weights)))
    sums = running[numpy.searchsorted(asks, ceilings, side="right")]
    return weights, numpy.where(sums > 0.0, sums, 1.0)


def _serve(requests: numpy.ndarray, left: numpy.ndarray, tiers: List[Tuple[int, int]],
           ) -> Tuple[numpy.ndarray, numpy.ndarray, numpy.ndarray]:
    """Every offer (a row) meets the requests sent to it (Mall_update_mall_stocks_sales_rationing_1): all are served if
    it holds enough, else tiers in turn. Returns (served, what is left of each offer, the requests not served)."""
    totals = requests.sum(axis=1)
    over = numpy.nonzero(totals > left)[0]
    after = left - totals
    if not len(over):
        return requests, after, numpy.zeros_like(requests)
    served = requests.copy()
    wanted = requests[over]
    remaining = left[over]
    tier_totals = numpy.add.reduceat(wanted, [start for start, _end in tiers], axis=1)
    for tier, (start, end) in enumerate(tiers):
        total = tier_totals[:, tier]
        enough = remaining >= total
        share = numpy.where(total > 0.0, numpy.where(enough, 1.0, remaining / numpy.where(total > 0.0, total, 1.0)), 0.0)
        served[over, start:end] = wanted[:, start:end] * share[:, None]
        remaining = numpy.where(enough, remaining - total, 0.0)
    after[over] = 0.0
    short = numpy.zeros_like(requests)
    gap = requests[over] - served[over]
    short[over] = numpy.where(gap > ROUNDING_SHARE * requests[over], gap, 0.0)
    return served, after, short


def allocate(bids: Sequence[Bid], offers: Sequence[Offer], asks: Sequence[float], schedule: DemandSchedule) -> Allocation:
    """Two rounds of choice among `offers` (asking `asks`, ascending) by `bids` (in tier order, `schedule` their demand)."""
    prices = numpy.array(asks, dtype=float)
    quantities = numpy.array([offer.quantity for offer in offers], dtype=float)
    ceilings = schedule.maximum_array()
    tiers, start = [], 0
    for _priority, group in groupby(bids, key=lambda bid: bid.priority):
        end = start + sum(1 for _ in group)
        tiers.append((start, end))
        start = end
    wants = schedule.matrix_at(prices)
    left = quantities.copy()

    stocked = left > ROUNDING_SHARE * quantities
    weights, sums = _weights(prices, stocked, ceilings)
    requests = wants * weights[:, None] / sums[None, :]
    requested = float(requests.sum())
    served, left, short = _serve(requests, left, tiers)
    taken = served.sum(axis=0)
    cost = prices @ served
    unmet = short.sum(axis=0)
    unmet_money = prices @ short

    stocked = left > ROUNDING_SHARE * quantities
    if stocked.any() and (unmet > 0.0).any():
        weights, sums = _weights(prices, stocked, ceilings)
        with numpy.errstate(all="ignore"):
            again = numpy.minimum(unmet[None, :], unmet_money[None, :] / prices[:, None])
        again = numpy.minimum(again, numpy.maximum(0.0, wants - taken[None, :]))
        again[:, unmet <= 0.0] = 0.0
        served, left, _short = _serve(again * weights[:, None] / sums[None, :], left, tiers)
        taken = taken + served.sum(axis=0)
        cost = cost + prices @ served
    return Allocation(taken.tolist(), cost.tolist(), (quantities - left).tolist(), requested)
