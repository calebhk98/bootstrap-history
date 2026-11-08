"""Demand that bids stand behind. A market starved by makers too small to supply it trades little, so
a newcomer sized to that trade stays small and the market never grows (Complaints/559). The part of a
market's bids that went unfilled at prices a newcomer's full cost per unit would still meet is real
demand; a gap no such bid backs is not, and the newcomer stays sized to the trade (entry_sizing.py)."""
import math
from typing import Callable, Optional, Sequence

from . import bid_columns, year_bids
from .entry_trial import recipes_by_cost
from .types import Bid, GoodId, TileId

# (recipe id, good, tile of the market, yearly output of the good the newcomer is built for) -> units of the good wanted at the
# recipe's full cost (on its newcomer's practised hours) and not traded
UnfilledAtCost = Callable[[str, GoodId, TileId, float], float]


def unfilled_from_columns(columns: bid_columns.BidColumns, cost_per_unit: float, traded_volume: float) -> float:
    """`unfilled_quantity` of a market's bids as columns."""
    if not math.isfinite(cost_per_unit) or cost_per_unit <= 0.0:
        return 0.0
    return max(0.0, bid_columns.sum_taken_at(columns, cost_per_unit) - max(0.0, traded_volume))


def unfilled_quantity(bids: Sequence[Bid], cost_per_unit: float, traded_volume: float) -> float:
    """What the bids take at a price of `cost_per_unit` (buyers who would pay less take nothing) beyond
    what the market traded."""
    return unfilled_from_columns(bid_columns.columns_of(bids), cost_per_unit, traded_volume)


def unfilled_at_cost(setup, record, view, area_map, bids_by_market, traded, costs=None) -> Optional[UnfilledAtCost]:
    """The year's unfilled demand a newcomer's full cost would meet, by recipe and market; None without bids. `bids_by_market` is the
    year's bids block (`year_bids.YearBids`) or a mapping of market to bids. With `costs` (entry_tables.EntryTables) a recipe is costed
    from the year's arrays."""
    if not bids_by_market:
        return None
    block = year_bids.of(bids_by_market)

    def unfilled(recipe_id: str, good: GoodId, tile: TileId, output_per_year: float) -> float:
        place = block.index.get((good, view.area_of(good, tile)))
        if place is None or not block.count(place):
            return 0.0
        costed = recipes_by_cost(setup, record, view, good, tile, [recipe_id], output_per_year, costs=costs)
        return unfilled_from_columns(block.columns_at(place), costed[0][1], traded(good, tile) or 0.0) if costed else 0.0
    return unfilled
