"""Demand that bids stand behind. A market starved by makers too small to supply it trades little, so
a newcomer sized to that trade stays small and the market never grows (Complaints/559). The part of a
market's bids that went unfilled at prices a newcomer's full cost per unit would still meet is real
demand; a gap no such bid backs is not, and the newcomer stays sized to the trade (entry_sizing.py)."""
import math
from typing import Callable, Mapping, Optional, Sequence, Tuple

from .entry_trial import recipes_by_cost
from .goods_market import quantity_at
from .types import AreaId, Bid, GoodId, TileId

# (recipe id, good, tile of the market) -> units of the good wanted at the recipe's full cost and not traded
UnfilledAtCost = Callable[[str, GoodId, TileId], float]


def unfilled_quantity(bids: Sequence[Bid], cost_per_unit: float, traded_volume: float) -> float:
    """What the bids take at a price of `cost_per_unit` (buyers who would pay less take nothing) beyond
    what the market traded."""
    if not math.isfinite(cost_per_unit) or cost_per_unit <= 0.0:
        return 0.0
    return max(0.0, math.fsum(quantity_at(bid, cost_per_unit) for bid in bids) - max(0.0, traded_volume))


def unfilled_at_cost(setup, record, view, area_map, bids_by_market: Mapping[Tuple[GoodId, AreaId], Sequence[Bid]],
                     traded) -> Optional[UnfilledAtCost]:
    """The year's unfilled demand a newcomer's full cost would meet, by recipe and market; None without bids."""
    if not bids_by_market:
        return None

    def unfilled(recipe_id: str, good: GoodId, tile: TileId) -> float:
        bids = bids_by_market.get((good, view.area_of(good, tile)))
        if not bids:
            return 0.0
        costed = recipes_by_cost(setup, record, view, good, tile, [recipe_id])
        return unfilled_quantity(bids, costed[0][1], traded(good, tile) or 0.0) if costed else 0.0
    return unfilled
