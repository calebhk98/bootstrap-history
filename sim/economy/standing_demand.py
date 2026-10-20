"""Demand that is settled outside the book but is still demand: a project's draw on a material, which the engine
pays at the market edge. Firm entry reads the year's bids (entry_year.py); these join them there, so a good only
such a buyer asks for draws a maker as a household's or a merchant's bid does. Nothing here clears."""
from typing import Dict, List, Mapping, Sequence, Tuple

from .types import AreaId, Bid, GoodId


def with_standing_bids(bids_by_market: Mapping[Tuple[GoodId, AreaId], Sequence[Bid]],
                       standing_bids: Sequence[Bid]) -> Dict[Tuple[GoodId, AreaId], List[Bid]]:
    """The year's bids by market with the standing bids added to their markets."""
    joined = {key: list(bids) for key, bids in bids_by_market.items()}
    for bid in standing_bids:
        joined.setdefault((bid.good, bid.area), []).append(bid)
    return joined
