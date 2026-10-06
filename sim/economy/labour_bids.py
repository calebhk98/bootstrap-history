"""An employer's bid for hours as tranches of falling marginal value, in the labour core's terms.

A single flat bid makes demand vertical over the range that matters and the wage jumps from floor to
ceiling (sim/labour/market/DESIGN.md, "Demand must slope"). Each hour is worth the bid's maximum wage
on average, the first tranches a little more and the last a little less.
"""
from typing import Iterable, List

from sim.constants import declare
from sim.labour.api import Bid

BID_TRANCHES = declare(
    "BID_TRANCHES", 4, kind="temporary_heuristic", unit="tranches of hours per bid", source=None, confidence="D",
    why="How finely an employer's falling marginal value of hours is cut. The real slope comes from the "
        "employer's output demand and technology, which a bid does not carry; a few steps keep demand "
        "from being vertical.")
BID_VALUE_SPREAD = declare(
    "BID_VALUE_SPREAD", 0.5, kind="temporary_heuristic",
    unit="share of the bid's maximum wage between first and last tranche", source=None, confidence="D",
    why="How far the last hour an employer takes is worth less than the first. Stands in for the fall in "
        "marginal value as an employer's output rises; not measured.")


def sloped_bids(bids: Iterable) -> List[Bid]:
    """Each economy bid as tranches whose maximum wages average the bid's own."""
    tranches = []
    for bid in bids:
        if bid.hours <= 0.0:
            continue
        for index in range(int(BID_TRANCHES)):
            position = (index + 0.5) / BID_TRANCHES
            tranches.append(Bid(employer=bid.employer, trade=bid.trade, area=bid.area,
                                hours=bid.hours / BID_TRANCHES,
                                maximum_wage=bid.maximum_wage * (1.0 + BID_VALUE_SPREAD * (0.5 - position))))
    return tranches
