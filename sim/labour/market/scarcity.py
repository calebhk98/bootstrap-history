"""What a trade can quote this year while its hands are few: more than the long-run training cost, because
trainees take years to arrive, but never more than employers' bids on the hours at stake or the cost of fetching
trained hands from elsewhere (Complaint 678)."""
import math
from typing import Optional, Sequence

from .records import Bid


def bid_weighted_worth(bids: Sequence[Bid], reservation: float) -> float:
    """The hours-weighted mean maximum wage of the bids that can pay the reservation wage: what the hours employers
    want are worth to them on the whole, so one stray bid with few hours does not set the wage. Never under the
    reservation wage."""
    live = [(bid.maximum_wage, bid.hours) for bid in bids if bid.maximum_wage >= reservation and bid.hours > 0.0]
    total = math.fsum(hours for _worth, hours in live)
    if total <= 0.0:
        return reservation
    return max(reservation, math.fsum(worth * hours for worth, hours in live) / total)


def short_run_ceiling(long_run: float, reservation: float, training_years: float, bids: Sequence[Bid],
                      imported: Optional[float], fetched_share: float = 1.0) -> float:
    """The most this year's wage can be. A trade needing no training has its hands move in at once, so its
    ceiling is the long-run cost. Otherwise the bid-weighted worth of the hours wanted, and where trained hands
    can be fetched from elsewhere, the hours that can come are capped at their cost and the rest of the hours wanted
    are not: the ceiling is the mean of the two weighted by `fetched_share`, the share of the hours wanted that can be
    fetched. Never under the reservation wage."""
    if math.isinf(long_run) or training_years <= 0.0 or not bids:
        ceiling = long_run
    else:
        ceiling = bid_weighted_worth(bids, reservation)
    if imported is not None:
        share = min(1.0, max(0.0, fetched_share))
        if share >= 1.0:
            ceiling = min(ceiling, imported)
        elif share > 0.0:
            if math.isinf(ceiling) and bids:
                ceiling = bid_weighted_worth(bids, reservation)      # hours left to the local market are worth what employers bid
            ceiling = (1.0 - share) * ceiling + share * min(ceiling, imported)
    return max(ceiling, reservation)
