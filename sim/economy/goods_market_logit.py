"""How a market's buyers are sent to its sellers: each buyer splits its demand over the sellers by the logit on their asks,
every seller sells at its own ask, and what a sold-out seller could not serve is sent again to the sellers still holding stock.

Follows Eurace@Unibi, Cons_Goods/Household_Consumer_Functions.c, Household_rank_and_buy_goods_1 and _2, and
Cons_Goods/Mall_functions.c, Mall_update_mall_stocks_sales_rationing_1 and _2:
  * round 1: a household weighs the sellers that have stock by exp(-intensity * log ask) and sends its weekly budget
    to one drawn by those weights (here its demand is split over all of them by the weights, the expectation of the
    draw: price_setting.choice_shares, the function sellers plan with);
  * a seller whose requests exceed its stock serves each by stock / requests (here lower priority tiers first, then
    pro rata, as goods_market_ration.ration does);
  * round 2 and on: a household that was rationed does the same among the sellers still holding stock, with the budget
    it has left, and is rationed again if need be, until no rationed household can reach a seller with stock (Eurace
    stops after round 2; here a buyer walks on to the next stall that has stock).
Eurace's households have one budget and no price-sensitive quantity; here a buyer's quantity at an ask is its schedule's
(Bid, goods_market.quantity_at), so a request is the buyer's quantity at that ask times its share, and in round 2 it is
the quantity unmet, limited by the budget unspent and by what the schedule still wants at the new ask. A buyer does not
choose a seller asking above its maximum price (Eurace has no such ceiling; the seller would only be sent buyers who
cannot take it).
"""
from typing import List, Sequence

import numpy

from . import goods_market_kernels
from .goods_market_demand import DemandSchedule
from .types import Bid, Offer


class Allocation:
    """What the logit choice gave: per bid, the quantity bought and what it cost at the asks; per offer, the quantity
    sold; the round-1 requests in all (what buyers asked for at the asks before any seller ran out); and `flow`, the
    quantity each offer (row) sold to each bid (column) over all rounds."""

    def __init__(self, quantity: List[float], cost: List[float], sold: List[float], requested: float,
                 flow: numpy.ndarray):
        self.quantity = quantity
        self.cost = cost
        self.sold = sold
        self.requested = requested
        self.flow = flow


def allocate(bids: Sequence[Bid], offers: Sequence[Offer], asks: Sequence[float], schedule: DemandSchedule) -> Allocation:
    """Rounds of choice among `offers` (asking `asks`, ascending) by `bids` (in tier order, `schedule` their demand);
    goods_market_kernels.allocate_arrays does the work."""
    quantities = numpy.fromiter((offer.quantity for offer in offers), dtype=float, count=len(offers))
    taken, cost, sold, requested, flow = goods_market_kernels.allocate_arrays(
        numpy.array(asks, dtype=float), quantities, *schedule.kernel_arrays(), schedule.tier_bounds())
    return Allocation(taken.tolist(), cost.tolist(), sold.tolist(), float(requested), flow)
