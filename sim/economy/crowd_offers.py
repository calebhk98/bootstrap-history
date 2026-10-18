"""A producer that stands for many workshops offers a rising supply schedule, not one flat ask (Complaint 550).

Its workshops differ in cost (producers.COST_SPREAD_WITHIN_PRODUCER, log-normal around the producer's cost), so
the cheap ones sell first and the dear ones only at a higher price: a bigger order pays more per unit. The
offer is cut into equal slices, each asking the producer's reservation scaled by the relative cost of the
workshops in that slice; the scale has a quantity-weighted mean of one, so the schedule is centred on the
price-taking reservation the producer would otherwise hold."""
import dataclasses
import math
from statistics import NormalDist
from typing import List

from sim.constants import declare

from .producers import COST_SPREAD_WITHIN_PRODUCER
from .types import Offer

CROWD_SCHEDULE_SLICES = declare(
    "CROWD_SCHEDULE_SLICES", 20, kind="temporary_heuristic", unit="equal slices of a crowd's offer",
    source=None, confidence="D", retire="Complaint 550",
    why="The log-normal cost spread of a crowd's workshops is a continuous supply curve; the clearing "
        "works on a few steps of it.")


def cost_factors(slices: int = int(CROWD_SCHEDULE_SLICES)) -> List[float]:
    """Relative cost of each equal slice of a crowd's workshops, cheapest first, with a mean of one."""
    spread = COST_SPREAD_WITHIN_PRODUCER
    normal = NormalDist()
    raw = [math.exp(spread * normal.inv_cdf((index + 0.5) / slices)) for index in range(slices)]
    mean = math.fsum(raw) / slices
    return [factor / mean for factor in raw]


def schedule(offer: Offer) -> List[Offer]:
    """`offer` cut into slices that ask more as the workshops get dearer. A reservation at or below zero (a
    perishable, a waste) is not a cost to scale and stays one offer."""
    if offer.reservation_price <= 0.0 or offer.quantity <= 0.0:
        return [offer]
    factors = cost_factors()
    share = offer.quantity / len(factors)
    return [dataclasses.replace(offer, quantity=share, reservation_price=offer.reservation_price * factor)
            for factor in factors]
